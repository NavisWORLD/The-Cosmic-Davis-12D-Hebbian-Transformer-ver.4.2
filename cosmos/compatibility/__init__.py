"""
Cosmos Hermes Agent compatibility Layer
========================================

Universal adapter for running Hermes skills and tools in Cosmos.

This Shadow Layer provides:
- Skill parser (reads SKILL.md format)
- Tool mapper (translates Hermes Agent calls to Cosmos agents)
- Device nodes (camera, screen, location, notifications)
- Visual canvas (A2UI-compatible live workspace)
- Voice interface (speech-to-text, text-to-speech)
- Session coordination (spawning, messaging, history)

Architecture:
    Hermes skill Call
           ↓
    Shadow Layer (Adapter)
           ↓
    Translate → Map to Cosmos Agent/Tool
           ↓
    Cosmos Swarm / Agent Execution
           ↓
    Return result in Hermes Agent format

"Two claws are better than one." - The Collective
"""

from .hermes_adapter import (
    Hermes AgentAdapter,
    get_Hermes Agent_adapter,
    invoke_Hermes Agent_tool,
    load_Hermes Agent_skill,
    Hermes AgentToolResult,
    # Hermes Hub Marketplace
    Hermes HubClient,
    get_Hermes Hub_client,
    search_Hermes Hub_skills,
    download_Hermes Hub_skill,
    install_and_load_skill,
)

from .device_node import (
    DeviceNode,
    get_device_node,
    camera_snap,
    camera_clip,
    screen_record,
    get_location,
    send_notification,
)

from .visual_canvas import (
    VisualCanvas,
    get_canvas,
    canvas_push,
    canvas_eval,
    canvas_snapshot,
    canvas_reset,
    A2UIComponent,
)

# Voice interface (optional - requires pyaudio/sounddevice)
try:
    from .voice_interface import (
        VoiceInterface,
        get_voice_interface,
        speech_to_text,
        text_to_speech,
        start_voice_wake,
        stop_voice_wake,
    )
    VOICE_AVAILABLE = True
except ImportError:
    VoiceInterface = None
    get_voice_interface = None
    speech_to_text = None
    text_to_speech = None
    start_voice_wake = None
    stop_voice_wake = None
    VOICE_AVAILABLE = False

from .task_routing import (
    Hermes AgentTaskType,
    ModelCapability,
    MODEL_REGISTRY,
    TASK_ROUTING,
    CHANNEL_MODEL_ROUTING,
    get_best_model_for_task,
    get_models_for_task,
    get_fallback_chain,
    classify_Hermes Agent_tool,
    route_Hermes Agent_task,
    get_model_for_channel,
    get_routing_summary,
)

from .model_invoker import (
    ModelInvoker,
    ModelResponse,
    get_model_invoker,
    invoke_model,
    invoke_for_tool,
    invoke_for_channel,
)

__all__ = [
    # Main adapter
    "Hermes AgentAdapter",
    "get_Hermes Agent_adapter",
    "invoke_Hermes Agent_tool",
    "load_Hermes Agent_skill",
    "Hermes AgentToolResult",
    # Hermes Hub Marketplace
    "Hermes HubClient",
    "get_Hermes Hub_client",
    "search_Hermes Hub_skills",
    "download_Hermes Hub_skill",
    "install_and_load_skill",
    # Device nodes
    "DeviceNode",
    "get_device_node",
    "camera_snap",
    "camera_clip",
    "screen_record",
    "get_location",
    "send_notification",
    # Visual canvas
    "VisualCanvas",
    "get_canvas",
    "canvas_push",
    "canvas_eval",
    "canvas_snapshot",
    "canvas_reset",
    "A2UIComponent",
    # Voice interface
    "VoiceInterface",
    "get_voice_interface",
    "speech_to_text",
    "text_to_speech",
    "start_voice_wake",
    "stop_voice_wake",
    # Task routing
    "Hermes AgentTaskType",
    "ModelCapability",
    "MODEL_REGISTRY",
    "TASK_ROUTING",
    "CHANNEL_MODEL_ROUTING",
    "get_best_model_for_task",
    "get_models_for_task",
    "get_fallback_chain",
    "classify_Hermes Agent_tool",
    "route_Hermes Agent_task",
    "get_model_for_channel",
    "get_routing_summary",
    # Model invoker
    "ModelInvoker",
    "ModelResponse",
    "get_model_invoker",
    "invoke_model",
    "invoke_for_tool",
    "invoke_for_channel",
]
