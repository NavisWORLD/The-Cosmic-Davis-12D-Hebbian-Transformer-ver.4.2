"""
<<<<<<< HEAD:cosmos/tools/__init__.py
cosmos Tools Package
=======
Farnsworth Tools Package
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/__init__.py

"Good news, everyone! I've invented tools that do the work for you!"

Comprehensive tooling for sysadmin, security, and productivity.
"""

from typing import Dict, Any

# Lazy imports to avoid circular dependencies
_sysadmin_tools = None
_security_tools = None


def get_sysadmin_tools():
    """Get sysadmin tools module."""
    global _sysadmin_tools
    if _sysadmin_tools is None:
<<<<<<< HEAD:cosmos/tools/__init__.py
        from cosmos.tools import sysadmin as _sysadmin_tools
=======
        from farnsworth.tools import sysadmin as _sysadmin_tools
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/__init__.py
    return _sysadmin_tools


def get_security_tools():
    """Get security tools module."""
    global _security_tools
    if _security_tools is None:
<<<<<<< HEAD:cosmos/tools/__init__.py
        from cosmos.tools import security as _security_tools
=======
        from farnsworth.tools import security as _security_tools
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/__init__.py
    return _security_tools


__all__ = [
    "get_sysadmin_tools",
    "get_security_tools",
]
