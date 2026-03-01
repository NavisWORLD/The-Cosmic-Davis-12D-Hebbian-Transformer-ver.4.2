"""
cosmos Integration Module

External tool and capability integration with:
- Dynamic tool routing and capability matching
- Multimodal input processing (vision, audio)
- Composio integration for 500+ tools
- Vision understanding (CLIP/BLIP)
- Voice interaction (Whisper/TTS)
"""

from cosmos.integration.tool_router import ToolRouter
from cosmos.integration.multimodal import MultimodalProcessor

# Vision capabilities
from cosmos.integration.vision import (
    VisionModule,
    VisionTask,
    VisionResult,
    ImageInput,
    SceneGraph,
)

# Voice capabilities
from cosmos.integration.voice import (
    VoiceModule,
    TranscriptionResult,
    TranscriptionSegment,
    VoiceCommand,
    AudioInput,
)

__all__ = [
    "ToolRouter",
    "MultimodalProcessor",
    # Vision
    "VisionModule",
    "VisionTask",
    "VisionResult",
    "ImageInput",
    "SceneGraph",
    # Voice
    "VoiceModule",
    "TranscriptionResult",
    "TranscriptionSegment",
    "VoiceCommand",
    "AudioInput",
]
