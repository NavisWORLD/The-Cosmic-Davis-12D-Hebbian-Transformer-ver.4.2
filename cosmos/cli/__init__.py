"""
<<<<<<< HEAD:cosmos/cli/__init__.py
cosmos CLI Module

Direct-to-user interfaces for easy interaction with cosmos.
"""

from .user_cli import cosmosCLI, run_user_cli
from .interactive import InteractiveShell
from .quick_actions import QuickActions

__all__ = [
    "cosmosCLI",
    "run_user_cli",
    "InteractiveShell",
    "QuickActions",
=======
Farnsworth CLI Module

Direct-to-user interfaces for easy interaction with Farnsworth.

AGI v1.8.4 Additions:
- RichCLI: Enhanced TUI with Rich/Textual
- SwarmSession: CLI-to-Swarm A2A sessions
"""

from .user_cli import FarnsworthCLI, run_user_cli
from .interactive import InteractiveShell
from .quick_actions import QuickActions
from .rich_cli import RichCLI, run_rich_cli
from .swarm_session import (
    SwarmSession,
    SwarmSessionManager,
    create_swarm_session,
    get_session_manager,
)

__all__ = [
    # Original
    "FarnsworthCLI",
    "run_user_cli",
    "InteractiveShell",
    "QuickActions",
    # AGI v1.8.4
    "RichCLI",
    "run_rich_cli",
    "SwarmSession",
    "SwarmSessionManager",
    "create_swarm_session",
    "get_session_manager",
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/cli/__init__.py
]
