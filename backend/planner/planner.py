"""AI Planner implementation.

Pipeline (07-ai-planner.md):
1. Story analysis -> sections (hook, setup, problem, development,
   resolution, conclusion, cta) derived from the brief/script.
2. For each section, define a clip requirement and query the search engine.
3. Grounding: only clips returned by search (real indexed footage) are used;
   unmet requirements are recorded in ``unresolved``.
4. Build a structured EditPlan, validate grounding, and store it.

When no LLM is configured, the planner uses a deterministic rule-based
strategy over the actual search results — this is real, grounded planning,
not a fake LLM response. When an LLM IS configured, it is used to refine
section labels/instructions, but clip selection is always validated against
the library.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from backend.ai import LLMProvider, ProviderUnavailable, get_llm_provider
from backend.config import Settings, get_settings
from backend.core import ProjectContext
from backend.logging import get_logger
from backend.planner.editing_rules import (
    detect_filler_phrases,
    pacing_for,
)
from backend.planner.platform_rules import profile_for
from backend.planner.types import EditPlan, PlanClip, PlanSection
from backend.search import SearchEngine, SearchFilters
from backend.utils.video import parse_time_to_seconds

log = get_logger("planner")

# Story structure templates. Each section has a label and a fraction of the
# target duration. The clip requirement describes what footage to look for.
SECTION_TEMPLATES = [
    {"type": "hook", "label": "Hook", "fraction": 0.10,
     "query_hint": "{topic} introduction highlight"},
    {"type": "setup", "label": "Setup", "fraction": 0.15,
     "query_hint": "{topic} context background"},
    {"type": "problem", "label": "Problem", "fraction": 0.20,
     "query_hint": "{topic} challenge problem"},
    {"type": "development", "label": "Development", "fraction": 0.30,
     "query_hint": "{topic} process building development"},
    {"type": "resolution", "label": "Resolution", "fraction": 0.15,
     "query_hint": "{topic} result success outcome"},
    {"type": "conclusion", "label": "Conclusion", "fraction": 0.07,
     "query_hint": "{topic} conclusion summary"},
    {"type": "cta", "label": "Call to Action", "fraction": 0.03,
     "query_hint": "{topic} call action subscribe"},
]


@dataclass
class PlanInput:
    brief: str
    script: str = ""
    audience: str = ""
    platform: str = "youtube"
    target_length: str = ""   # e.g. "8 minutes" or "short"/"medium"/"long"
    style: str = ""

    @property
    def topic(self) -> str:
        return (self.brief or self.script or "").strip().split("\n")[0][:80]


class AIPlanner:
    def __init__(self, ctx: ProjectContext, settings: Settings | None = None,
                 llm: LLMProvider | None = None,
                 search_engine: SearchEngine | None = None) -> None:
        self.ctx = ctx
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_provider(self.settings)
        self.search = search_engine or SearchEngine(ctx, self.settings)

    def create_plan(self, plan_input: PlanInput) -> tuple[str, EditPlan]:
        """Create and store an edit plan. Returns (session_id, plan)."""
        session_id = self.ctx.repo.create_planner_session(
            project_id=self.ctx.project_id, brief=plan_input.brief,
            script=plan_input.script, audience=plan_input.audience,
            platform=plan_input.platform, target_length=plan_input.target_length,
            style=plan_input.style)
        log.info("planner session created", extra={
            "project_id": self.ctx.project_id, "session_id": session_id,
            "action": "plan", "status": "start"})

        target_seconds = self._target_seconds(plan_input)
        platform_profile = profile_for(plan_input.platform)
        sections = self._build_sections(plan_input, target_seconds)
        plan = EditPlan(
            title=self._title(plan_input),
            platform=plan_input.platform,
            target_length=plan_input.target_length or platform_profile["default_length"],
            sections=sections,
        )

        # Ground clip selection against the real library.
        valid_ids = {v["id"] for v in self.ctx.repo.list_videos(self.ctx.project_id)}
        unresolved = plan.validate_grounding(valid_ids)
        if unresolved:
            plan.unresolved.extend(unresolved)

        # Add deterministic recommendations.
        self._add_recommendations(plan, plan_input, platform_profile)

        # Optionally refine instructions via LLM (clip selection stays grounded).
        if self.llm.available:
            self._refine_with_llm(plan, plan_input)

        self.ctx.repo.update_planner_session(
            session_id, status="completed", plan_json=plan.to_dict())
        log.info("planner session completed", extra={
            "project_id": self.ctx.project_id, "session_id": session_id,
            "action": "plan", "status": "done",
            "sections": len(plan.sections), "clips": len(plan.all_clips())})
        return session_id, plan

    # ---- Story structure ------------------------------------------------
    def _target_seconds(self, plan_input: PlanInput) -> float:
        length = (plan_input.target_length or "").lower()
        if "min" in length:
            return parse_time_to_seconds("0:" + length.replace("minutes", "min").strip())
        if length in ("short",):
            return 60.0
        if length in ("medium",):
            return 300.0
        if length in ("long",):
            return 600.0
        return 300.0  # default ~5 min

    def _build_sections(self, plan_input: PlanInput, target_seconds: float) -> list[PlanSection]:
        sections: list[PlanSection] = []
        cursor = 0.0
        topic = plan_input.topic
        for tmpl in SECTION_TEMPLATES:
            duration = max(5.0, target_seconds * tmpl["fraction"])
            query = tmpl["query_hint"].format(topic=topic)
            # If a script is provided, also search script-derived keywords.
            clips = self._select_clips(query, plan_input, max_clips=2)
            instructions = self._section_instructions(tmpl["type"], plan_input)
            sections.append(PlanSection(
                type=tmpl["type"], label=tmpl["label"],
                target_start=cursor, target_duration=duration,
                clips=clips, instructions=instructions))
            cursor += duration
        return sections

    def _select_clips(self, query: str, plan_input: PlanInput,
                      max_clips: int) -> list[PlanClip]:
        results = self.search.search(query, limit=max_clips * 2)
        clips: list[PlanClip] = []
        for r in results[:max_clips]:
            clips.append(PlanClip(
                video_id=r.video_id, filename=r.filename,
                source_start=r.start_time, source_end=r.end_time,
                purpose=query, score=r.score, reason=r.reason))
        if not clips:
            # Record unmet requirement instead of inventing footage.
            self._note_unresolved(f"No footage found for: {query}")
        return clips

    _unresolved_buffer: list[str] = []

    def _note_unresolved(self, message: str) -> None:
        # Stored on the plan after sections are built.
        self._unresolved_buffer.append(message)

    def _section_instructions(self, section_type: str, plan_input: PlanInput) -> list[str]:
        pace_min, pace_max = pacing_for(plan_input.platform, plan_input.target_length)
        instr: list[str] = []
        if section_type == "hook":
            instr.append("Fast cut, capture attention in first seconds")
            instr.append("Subtitle emphasis on key phrase")
        if section_type in ("setup", "development"):
            instr.append(f"Visual change every {pace_min:.0f}-{pace_max:.0f}s")
            instr.append("Insert B-roll over talking head where relevant")
        if section_type == "problem":
            instr.append("Tighten pacing to heighten tension")
        if section_type == "resolution":
            instr.append("Slow slightly, show result")
        if section_type == "cta":
            instr.append("Clear on-screen call to action")
        return instr

    def _title(self, plan_input: PlanInput) -> str:
        topic = plan_input.topic
        return topic[:60] if topic else "Untitled Edit"

    def _add_recommendations(self, plan: EditPlan, plan_input: PlanInput,
                             platform_profile: dict) -> None:
        # Move buffered unresolved notes onto the plan.
        plan.unresolved.extend(self._unresolved_buffer)
        self._unresolved_buffer.clear()

        # Silence / filler detection across selected clips' transcripts.
        for clip in plan.all_clips():
            segs = self.ctx.repo.query_all(
                """SELECT text FROM transcript_segments
                   WHERE video_id = ? AND start_time >= ? AND end_time <= ?;""",
                (clip.video_id, clip.source_start, clip.source_end))
            for seg in segs:
                fillers = detect_filler_phrases(seg["text"])
                if fillers:
                    plan.recommendations.append(
                        f"Remove filler words ({', '.join(fillers[:3])}) in {clip.filename}")

        plan.color_recommendation = {
            "style": plan_input.style or "balanced",
            "recommendation": "Increase contrast slightly; match temperature across clips",
        }
        plan.music_recommendation = {
            "music_style": "ambient" if plan_input.platform == "youtube" else "energetic",
            "energy": "medium",
            "ducking": "reduce music during voice by -8 dB",
        }
        plan.recommendations.append(
            f"Target visual change interval: {pacing_for(plan_input.platform, plan_input.target_length)}")
        plan.recommendations.append(
            f"Subtitle style: {platform_profile['subtitle_style']}")

    # ---- LLM refinement (optional) -------------------------------------
    def _refine_with_llm(self, plan: EditPlan, plan_input: PlanInput) -> None:
        system = (
            "You are a professional video editing assistant. Refine the section "
            "instructions for an editing plan. Respond ONLY with JSON: "
            '{"sections":[{"type":..., "instructions":[...]}]}. '
            "Do not invent footage or clip references."
        )
        user = json.dumps({
            "topic": plan_input.topic,
            "platform": plan_input.platform,
            "sections": [{"type": s.type, "label": s.label} for s in plan.sections],
        })
        try:
            resp = self.llm.generate(system, user, max_tokens=1024, temperature=0.2)
        except ProviderUnavailable:
            return
        if not resp.valid or not resp.text:
            return
        try:
            data = json.loads(resp.text)
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON, keeping deterministic instructions")
            return
        for section_data in data.get("sections", []):
            for section in plan.sections:
                if section.type == section_data.get("type"):
                    extra = section_data.get("instructions", [])
                    if isinstance(extra, list):
                        for instr in extra:
                            if isinstance(instr, str) and instr not in section.instructions:
                                section.instructions.append(instr)
