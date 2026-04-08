"""
cosmos Web Interface
Token-gated chat with glassmorphism UI
"""

# NOTE: We intentionally do NOT import from .server here at module level.
# server.py is a heavy module (torch, scipy, ollama, mediapipe, faiss, …)
# that takes a long time to import.  Consumers that need the app or main
# should import directly:  `from cosmos.web.server import app`
# or `import cosmos.web.server`.

__all__ = ["app", "main"]
