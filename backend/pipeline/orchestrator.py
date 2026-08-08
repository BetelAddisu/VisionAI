"""Analysis pipeline orchestrator.

Runs the per-video stages in order, recording status in analysis_state so
processing resumes from the last incomplete stage. Stages are skipped when
already completed; failed stages are retried up to max_retries.

Stages: metadata -> scenes -> audio -> transcription -> frames ->
quality -> embeddings. Vision/objects are optional and skipped when the
vision provider is unavailable (handled cleanly, never faked).
"""
from __future__ import annotations

from pathlib import Path

from backend.ai import (
    EmbeddingProvider,
    ProviderUnavailable,
    SpeechProvider,
    VisionProvider,
    get_embedding_provider,
    get_speech_provider,
    get_vision_provider,
)
from backend.config import Settings, get_settings
from backend.core import ProjectContext
from backend.indexing.thumbnails import generate_scene_thumbnail
from backend.logging import get_logger
from backend.pipeline.stages.audio import extract_audio
from backend.pipeline.stages.audio_analysis import analyze_audio
from backend.pipeline.stages.embeddings import embed_transcript_segments
from backend.pipeline.stages.frames import sample_frames
from backend.pipeline.stages.quality import analyze_quality
from backend.pipeline.stages.scenes import detect_scenes
from backend.pipeline.stages.transcription import transcribe_audio

log = get_logger("pipeline")

STAGES = ["scenes", "audio", "transcription", "frames", "quality", "embeddings"]


class AnalysisPipeline:
    def __init__(self, ctx: ProjectContext, settings: Settings | None = None,
                 speech: SpeechProvider | None = None,
                 vision: VisionProvider | None = None,
                 embeddings: EmbeddingProvider | None = None) -> None:
        self.ctx = ctx
        self.settings = settings or get_settings()
        self.speech = speech or get_speech_provider(self.settings)
        self.vision = vision or get_vision_provider(self.settings)
        self.embeddings = embeddings or get_embedding_provider(self.settings)

    def analyze(self, video_id: str, *, force: bool = False) -> dict:
        """Run all pending stages for a video. Returns a status summary."""
        video = self.ctx.repo.get_video(video_id)
        if not video:
            raise FileNotFoundError(f"Video not found: {video_id}")
        if not video.get("available"):
            raise RuntimeError(f"Video unavailable on disk: {video_id}")

        if force:
            for stage in STAGES:
                self.ctx.repo.set_stage_status(video_id, stage, "pending")

        summary = {"video_id": video_id, "stages": {}}
        for stage in STAGES:
            status = self._run_stage(stage, video)
            summary["stages"][stage] = status
            if status == "failed":
                # Continue to next stages rather than aborting everything.
                continue
        all_done = all(
            self.ctx.repo.get_stage_status(video_id, s) in ("completed", "skipped")
            for s in STAGES
        )
        self.ctx.repo.update_video(video_id, analyzed=1 if all_done else 0)
        return summary

    def _run_stage(self, stage: str, video: dict) -> str:
        current = self.ctx.repo.get_stage_status(video["id"], stage)
        if current == "completed":
            return "completed"
        self.ctx.repo.set_stage_status(video["id"], stage, "running")
        try:
            getattr(self, f"_stage_{stage}")(video)
            self.ctx.repo.set_stage_status(video["id"], stage, "completed", progress=1.0)
            return "completed"
        except ProviderUnavailable as exc:
            # Clean unavailable state: mark skipped, not failed.
            self.ctx.repo.set_stage_status(
                video["id"], stage, "skipped", error=str(exc))
            log.info("stage skipped (provider unavailable)", extra={
                "video_id": video["id"], "stage": stage, "error": str(exc)})
            return "skipped"
        except FileNotFoundError as exc:
            # e.g. no audio stream: skip gracefully.
            self.ctx.repo.set_stage_status(
                video["id"], stage, "skipped", error=str(exc))
            log.info("stage skipped", extra={
                "video_id": video["id"], "stage": stage, "error": str(exc)})
            return "skipped"
        except Exception as exc:  # noqa: BLE001
            retries = self.ctx.repo.increment_retry(video["id"], stage)
            max_retries = self.settings.pipeline.max_retries
            if retries < max_retries:
                self.ctx.repo.set_stage_status(
                    video["id"], stage, "pending", error=str(exc))
                log.warning("stage failed (will retry)", extra={
                    "video_id": video["id"], "stage": stage,
                    "retry": retries, "error": str(exc)})
                return "pending"
            self.ctx.repo.set_stage_status(
                video["id"], stage, "failed", error=str(exc))
            log.error("stage failed", extra={
                "video_id": video["id"], "stage": stage, "error": str(exc)})
            return "failed"

    # ---- Stage implementations -----------------------------------------
    def _stage_scenes(self, video: dict) -> None:
        self.ctx.repo.clear_scenes(video["id"])
        scenes = detect_scenes(
            video["path"], threshold=self.settings.pipeline.scene_threshold)
        for i, (start, end) in enumerate(scenes):
            thumb = None
            try:
                thumb_dir = Path(self.ctx.cache_path) / "scenes"
                thumb_path = thumb_dir / f"{video['id']}_scene_{i+1}.jpg"
                mid = (start + end) / 2
                generate_scene_thumbnail(video["path"], thumb_path, at_seconds=mid,
                                          settings=self.settings)
                thumb = str(thumb_path)
            except Exception as exc:  # noqa: BLE001
                log.debug("scene thumbnail skipped", extra={"error": str(exc)})
            self.ctx.repo.add_scene(
                video_id=video["id"], scene_number=i + 1,
                start_time=start, end_time=end, thumbnail_path=thumb)

    def _stage_audio(self, video: dict) -> None:
        audio_dir = Path(self.ctx.cache_path) / "audio"
        audio_path = audio_dir / f"{video['id']}.wav"
        extract_audio(
            video["path"], audio_path,
            sample_rate=self.settings.pipeline.audio_sample_rate,
            channels=self.settings.pipeline.audio_channels)

    def _stage_transcription(self, video: dict) -> None:
        self.ctx.repo.clear_transcript(video["id"])
        audio_path = Path(self.ctx.cache_path) / "audio" / f"{video['id']}.wav"
        if not audio_path.exists():
            # Audio stage may have been skipped (no audio) — nothing to do.
            if not video.get("has_audio"):
                return
            raise FileNotFoundError(f"Audio not found: {audio_path}")
        segments = transcribe_audio(audio_path, self.speech)
        for seg in segments:
            self.ctx.repo.add_transcript_segment(
                video_id=video["id"], start_time=seg.start, end_time=seg.end,
                text=seg.text, confidence=seg.confidence, speaker=seg.speaker,
                language=seg.language)
        # Unload the speech model to free RAM before the next heavy stage.
        if hasattr(self.speech, "unload"):
            self.speech.unload()

    def _stage_frames(self, video: dict) -> None:
        self.ctx.repo.clear_frames(video["id"])
        frame_dir = Path(self.ctx.cache_path) / "frames" / video["id"]
        frames = sample_frames(
            video["path"], frame_dir,
            interval=self.settings.pipeline.frame_sample_interval,
            width=self.settings.pipeline.thumbnail_width)
        for t, path in frames:
            self.ctx.repo.add_frame(video_id=video["id"], timestamp=t, image_path=path)

    def _stage_quality(self, video: dict) -> None:
        for frame in self.ctx.repo.list_frames(video["id"]):
            metrics = analyze_quality(frame["image_path"])
            self.ctx.repo.add_quality(frame_id=frame["id"], **metrics)

    def _stage_embeddings(self, video: dict) -> None:
        segments_rows = self.ctx.repo.list_transcript(video["id"])
        from backend.ai.base import TranscriptSegment
        segments = [TranscriptSegment(
            start=r["start_time"], end=r["end_time"], text=r["text"],
            confidence=r["confidence"], language=r["language"])
            for r in segments_rows]
        embed_transcript_segments(self.ctx, video["id"], segments, self.embeddings)
