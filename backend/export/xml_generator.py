"""DaVinci Resolve / Final Cut Pro 7 XML generator.

Produces an xmeml document that DaVinci Resolve can import via
File > Import Timeline. Preserves source media path, source in/out points,
timeline position and track structure. Paths are encoded as file URLs.
"""
from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from backend.logging import get_logger
from backend.timeline.models import Timeline
from backend.utils.video import format_timestamp

log = get_logger("xml_export")


def _file_url(path: str) -> str:
    # DaVinci accepts file:// URLs and also plain OS paths in <pathurl>.
    p = Path(path)
    return p.as_uri()


def _tc(seconds: float, fps: float) -> str:
    """Convert seconds to a timecode string HH:MM:SS:FF (frame-based)."""
    if fps <= 0:
        fps = 30.0
    total_frames = int(round(seconds * fps))
    frames_per_hour = int(round(fps * 3600))
    frames_per_minute = int(round(fps * 60))
    hours = total_frames // frames_per_hour
    remaining = total_frames % frames_per_hour
    minutes = remaining // frames_per_minute
    remaining %= frames_per_minute
    secs = remaining // int(round(fps))
    frames = remaining % int(round(fps))
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


def generate_davinci_xml(timeline: Timeline, output_path: str | Path) -> Path:
    """Write the timeline as Final Cut Pro 7 XML (xmeml)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fps = timeline.fps or 30.0

    xmeml = Element("xmeml", version="5")
    sequence = SubElement(xmeml, "sequence")
    SubElement(sequence, "name").text = timeline.name or "AI Edit"
    SubElement(sequence, "duration").text = str(int(timeline.duration * fps))
    rate = SubElement(sequence, "rate")
    SubElement(rate, "timebase").text = str(int(round(fps)))
    SubElement(rate, "ntsc").text = "FALSE"

    media = SubElement(sequence, "media")
    video = SubElement(media, "video")
    SubElement(video, "format")  # placeholder
    video_tracks = SubElement(video, "track")
    audio = SubElement(media, "audio")
    audio_tracks = SubElement(audio, "track")

    # Group clips by track type.
    video_clips = [c for c in timeline.clips if c.track.startswith("V")]
    audio_clips = [c for c in timeline.clips if c.track.startswith("A")]

    for clip in video_clips:
        _add_clipitem(video_tracks, clip, fps, kind="video")
    for clip in audio_clips:
        _add_clipitem(audio_tracks, clip, fps, kind="audio")

    # Pretty-print with declaration.
    xml_bytes = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(xmeml, encoding="utf-8")
    output_path.write_bytes(xml_bytes)
    log.info("davinci xml exported", extra={
        "action": "export_xml", "status": "done",
        "timeline_id": timeline.id, "path": str(output_path),
        "clips": len(timeline.clips)})
    return output_path


def _add_clipitem(parent: Element, clip, fps: float, *, kind: str) -> None:
    clipitem = SubElement(parent, "clipitem", id=f"clip-{clip.id}")
    SubElement(clipitem, "name").text = clip.filename or clip.label
    SubElement(clipitem, "enabled").text = "TRUE"
    SubElement(clipitem, "duration").text = str(int((clip.timeline_end - clip.timeline_start) * fps))
    rate = SubElement(clipitem, "rate")
    SubElement(rate, "timebase").text = str(int(round(fps)))
    SubElement(rate, "ntsc").text = "FALSE"
    start = SubElement(clipitem, "start").text = str(int(clip.timeline_start * fps))
    end = SubElement(clipitem, "end").text = str(int(clip.timeline_end * fps))
    in_node = SubElement(clipitem, "in").text = str(int(clip.source_start * fps))
    out_node = SubElement(clipitem, "out").text = str(int(clip.source_end * fps))
    file_el = SubElement(clipitem, "file", id=f"file-{clip.video_id}")
    SubElement(file_el, "name").text = clip.filename
    SubElement(file_el, "pathurl").text = _file_url(clip.source_path)
    if kind == "video":
        SubElement(clipitem, "itemtype").text = "video"
    else:
        SubElement(clipitem, "itemtype").text = "audio"
