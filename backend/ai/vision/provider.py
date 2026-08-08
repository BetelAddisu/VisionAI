"""Vision provider: describes image frames.

Default is the None provider (vision models are heavy for the target
hardware). A real local provider can be swapped in via config without
rewriting the pipeline.
"""
from __future__ import annotations

from backend.ai.base import ProviderUnavailable, VisionDescription, VisionProvider
from backend.config import Settings, get_settings


class NoneVisionProvider(VisionProvider):
    @property
    def available(self) -> bool:
        return False

    @property
    def model_version(self) -> str:
        return "none"

    def describe_frame(self, image_path: str) -> VisionDescription:
        raise ProviderUnavailable("No vision provider configured")


def get_vision_provider(settings: Settings | None = None) -> VisionProvider:
    settings = settings or get_settings()
    # Only "none" is wired by default; advanced vision is a future phase.
    return NoneVisionProvider()
