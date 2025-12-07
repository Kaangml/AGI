"""
EVO-TR Web API

FastAPI backend for EVO-TR chat system.
Provides REST API and WebSocket endpoints.
"""

from .app import app, create_app

__all__ = ["app", "create_app"]
