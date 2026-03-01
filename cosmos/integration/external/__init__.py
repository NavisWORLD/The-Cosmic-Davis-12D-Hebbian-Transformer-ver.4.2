"""
<<<<<<< HEAD:cosmos/integration/external/__init__.py
cosmos External AI Provider Integrations.
=======
Farnsworth External AI Provider Integrations.
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/external/__init__.py

This module provides integrations with external AI services:
- Claude Code CLI (Anthropic, via authenticated CLI)
- Kimi (Moonshot AI, long-context reasoning)
- Grok (xAI)
- And more...

These providers participate in the multi-model swarm orchestration.
"""

from .base import ExternalProvider, IntegrationConfig, ConnectionStatus

# Lazy imports for optional providers
__all__ = [
    "ExternalProvider",
    "IntegrationConfig",
    "ConnectionStatus",
]
