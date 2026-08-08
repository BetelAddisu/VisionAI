"""Platform rules: per-platform editing strategies."""
from __future__ import annotations

PLATFORM_PROFILES = {
    "youtube": {
        "focus": ["storytelling", "retention", "chapters", "pacing"],
        "subtitle_style": "youtube",
        "default_length": "long",
    },
    "tiktok": {
        "focus": ["immediate_hook", "fast_pacing", "subtitles", "visual_changes"],
        "subtitle_style": "shorts",
        "default_length": "short",
    },
    "shorts": {
        "focus": ["immediate_hook", "fast_pacing", "subtitles", "visual_changes"],
        "subtitle_style": "shorts",
        "default_length": "short",
    },
    "linkedin": {
        "focus": ["professional_storytelling", "credibility", "clear_message"],
        "subtitle_style": "clean",
        "default_length": "medium",
    },
    "default": {
        "focus": ["clear_message", "pacing"],
        "subtitle_style": "clean",
        "default_length": "medium",
    },
}


def profile_for(platform: str) -> dict:
    return PLATFORM_PROFILES.get(platform.lower(), PLATFORM_PROFILES["default"])
