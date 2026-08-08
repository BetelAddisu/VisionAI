"""Entrypoint: run the VisionAI backend server.

Usage:
    python -m backend.main            # default host/port from config
    uvicorn backend.main:app --reload
"""
from __future__ import annotations

import sys

from backend.api import create_app
from backend.app_container import create_container
from backend.config import get_settings

app = create_app(create_container())


def main() -> None:
    import uvicorn
    settings = get_settings()
    host = sys.argv[1] if len(sys.argv) > 1 else settings.server.host
    port = int(sys.argv[2]) if len(sys.argv) > 2 else settings.server.port
    uvicorn.run("backend.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
