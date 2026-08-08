"""High-level DaVinci export: writes XML + SRT sidecar, marks exported."""
from __future__ import annotations

from pathlib import Path

from backend.core import ProjectContext
from backend.export.xml_generator import generate_davinci_xml
from backend.timeline.models import Timeline
from backend.timeline.subtitles import to_srt


def export_davinci_xml(ctx: ProjectContext, timeline: Timeline,
                       *, version: int = 1) -> dict:
    """Export the timeline to DaVinci XML plus an SRT subtitle sidecar.

    Never overwrites a previous export: each export is versioned.
    Returns a dict with the output paths.
    """
    exports_dir = Path(ctx.exports_path) / "xml"
    exports_dir.mkdir(parents=True, exist_ok=True)
    base = f"{timeline.name.replace(' ', '_')}_{timeline.id[:8]}_v{version}"
    xml_path = exports_dir / f"{base}.xml"
    generate_davinci_xml(timeline, xml_path)

    srt_path = None
    if timeline.subtitles:
        srt_dir = Path(ctx.exports_path) / "srt"
        srt_dir.mkdir(parents=True, exist_ok=True)
        srt_path = srt_dir / f"{base}.srt"
        srt_path.write_text(to_srt(timeline.subtitles), encoding="utf-8")

    ctx.repo.mark_timeline_exported(timeline.id)
    return {"xml": str(xml_path), "srt": str(srt_path) if srt_path else None,
            "timeline_id": timeline.id, "version": version}


def export_srt(ctx: ProjectContext, timeline: Timeline) -> str:
    """Export subtitles only as SRT."""
    srt_dir = Path(ctx.exports_path) / "srt"
    srt_dir.mkdir(parents=True, exist_ok=True)
    path = srt_dir / f"{timeline.name.replace(' ', '_')}_{timeline.id[:8]}.srt"
    path.write_text(to_srt(timeline.subtitles), encoding="utf-8")
    return str(path)
