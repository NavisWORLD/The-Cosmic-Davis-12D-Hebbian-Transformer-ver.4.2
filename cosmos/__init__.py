"""
cosmos: Self-Evolving Companion AI

A modular, self-evolving companion AI that runs entirely locally with zero-cost operation.
Features MemGPT-style memory paging, LangGraph agent swarms, and genetic evolution.
"""

__version__ = "2.1.0-alpha"
__author__ = "cosmos Team"

from cosmos.core.nexus import nexus, Signal, SignalType
from cosmos.core.fcp import FCPEngine
from cosmos.core.neuromorphic.engine import neuro_engine
from cosmos.os_integration.bridge import os_bridge
from cosmos.core.cognition.theory_of_mind import tom_engine

__all__ = [
    "nexus", "Signal", "SignalType",
    "FCPEngine",
    "neuro_engine",
    "os_bridge",
    "tom_engine",
    "__version__",
]
