"""
cosmos Collaboration Module

Team collaboration features for multi-user cosmos deployments:
- Shared Memory Pools
- Multi-User Support
- Permission-Based Access Control
- Collaborative Sessions
"""

from cosmos.collaboration.shared_memory import (
    SharedMemoryPool,
    MemoryPermission,
    MemoryAccess,
)
from cosmos.collaboration.multi_user import (
    UserManager,
    UserProfile,
    UserSession,
    UserRole,
)
from cosmos.collaboration.permissions import (
    PermissionManager,
    Permission,
    PermissionLevel,
    AccessControl,
)
from cosmos.collaboration.sessions import (
    CollaborativeSession,
    SessionManager,
    SessionEvent,
    SessionState,
)

__all__ = [
    # Shared Memory
    "SharedMemoryPool",
    "MemoryPermission",
    "MemoryAccess",
    # Multi-User
    "UserManager",
    "UserProfile",
    "UserSession",
    "UserRole",
    # Permissions
    "PermissionManager",
    "Permission",
    "PermissionLevel",
    "AccessControl",
    # Sessions
    "CollaborativeSession",
    "SessionManager",
    "SessionEvent",
    "SessionState",
]
