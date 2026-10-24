"""
cosmos Web Interface.

Web-server objects are loaded lazily so model/library imports do not require
FastAPI or start importing the HTTP stack as a side effect.
"""

__all__ = ["app", "main"]


def __getattr__(name):
    if name in {"app", "main"}:
        from .server import app, main
        return {"app": app, "main": main}[name]
    raise AttributeError(name)
