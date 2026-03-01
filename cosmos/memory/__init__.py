"""
cosmos Memory Module

MemGPT-style hierarchical memory system with:
- Virtual context window paging
- Attention-weighted importance scoring
- Graph-augmented semantic retrieval
- Background "dreaming" consolidation

Q1 2025 (v0.2.0) Features:
- Episodic memory timeline
- Semantic memory layers with concept hierarchies
- Memory sharing (export/import)
- Enhanced knowledge graph with temporal edges
"""

from cosmos.memory.virtual_context import VirtualContext, ContextWindow, PageManager
from cosmos.memory.working_memory import WorkingMemory
from cosmos.memory.archival_memory import ArchivalMemory
from cosmos.memory.recall_memory import RecallMemory
from cosmos.memory.knowledge_graph import KnowledgeGraph
from cosmos.memory.memory_dreaming import MemoryDreamer
from cosmos.memory.memory_system import MemorySystem

# Q1 2025 Features
from cosmos.memory.episodic_memory import (
    EpisodicMemory,
    Episode,
    Session,
    EventType,
    TimelineQuery,
    OnThisDayResult,
)
from cosmos.memory.semantic_layers import (
    SemanticLayerSystem,
    SemanticConcept,
    AbstractionLevel,
    DomainCluster,
    CrossDomainConnection,
)
from cosmos.memory.memory_sharing import (
    MemorySharing,
    ExportFormat,
    MergeStrategy,
    ExportManifest,
    ImportResult,
    BackupInfo,
)
from cosmos.memory.knowledge_graph_v2 import (
    KnowledgeGraphV2,
    TemporalEdge,
    EntityCluster,
    EntityResolutionCandidate,
)
from cosmos.memory.conversation_export import (
    ConversationExporter,
    ConversationExportFormat,
    ExportOptions,
    ExportResult,
)
from cosmos.memory.project_tracking import (
    ProjectTracker,
    Project,
    Task,
    Milestone,
    ProjectLink,
    ProjectStatus,
    TaskStatus,
    MilestoneType,
    LinkType,
)
from cosmos.memory.dream_consolidation import (
    DreamConsolidator,
    DreamPhase,
    ConsolidationStrategy,
    MemoryTrace,
    DreamSequence,
    ConsolidationCycle,
)

__all__ = [
    # Core memory components
    "VirtualContext",
    "ContextWindow",
    "PageManager",
    "WorkingMemory",
    "ArchivalMemory",
    "RecallMemory",
    "KnowledgeGraph",
    "MemoryDreamer",
    "MemorySystem",
    # Q1 2025: Episodic Memory
    "EpisodicMemory",
    "Episode",
    "Session",
    "EventType",
    "TimelineQuery",
    "OnThisDayResult",
    # Q1 2025: Semantic Layers
    "SemanticLayerSystem",
    "SemanticConcept",
    "AbstractionLevel",
    "DomainCluster",
    "CrossDomainConnection",
    # Q1 2025: Memory Sharing
    "MemorySharing",
    "ExportFormat",
    "MergeStrategy",
    "ExportManifest",
    "ImportResult",
    "BackupInfo",
    # Q1 2025: Enhanced Knowledge Graph
    "KnowledgeGraphV2",
    "TemporalEdge",
    "EntityCluster",
    "EntityResolutionCandidate",
    # Conversation Export
    "ConversationExporter",
    "ConversationExportFormat",
    "ExportOptions",
    "ExportResult",
    # Project Tracking
    "ProjectTracker",
    "Project",
    "Task",
    "Milestone",
    "ProjectLink",
    "ProjectStatus",
    "TaskStatus",
    "MilestoneType",
    "LinkType",
    # Advanced Dream Consolidation
    "DreamConsolidator",
    "DreamPhase",
    "ConsolidationStrategy",
    "MemoryTrace",
    "DreamSequence",
    "ConsolidationCycle",
]
