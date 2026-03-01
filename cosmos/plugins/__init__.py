"""
<<<<<<< HEAD:cosmos/plugins/__init__.py
cosmos Plugin System
=======
Farnsworth Plugin System
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/plugins/__init__.py

Extensible plugin architecture for adding custom functionality.
"""

from .base import Plugin, PluginManager, PluginMetadata, PluginStatus
from .loader import PluginLoader
from .registry import plugin_registry

__all__ = [
    "Plugin",
    "PluginManager",
    "PluginMetadata",
    "PluginStatus",
    "PluginLoader",
    "plugin_registry",
]
