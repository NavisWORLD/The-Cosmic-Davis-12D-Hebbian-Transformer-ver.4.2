"""
<<<<<<< HEAD:cosmos/automation/__init__.py
cosmos Automation Module
=======
Farnsworth Automation Module
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/automation/__init__.py

Workflow automation, scheduling, and integration capabilities.
"""

from .workflow_builder import WorkflowBuilder, Workflow, WorkflowStep
from .n8n_enhanced import EnhancedN8nIntegration, N8nWorkflow, N8nNode
from .scheduler import TaskScheduler, ScheduledTask
from .triggers import TriggerManager, Trigger, TriggerType

__all__ = [
    "WorkflowBuilder",
    "Workflow",
    "WorkflowStep",
    "EnhancedN8nIntegration",
    "N8nWorkflow",
    "N8nNode",
    "TaskScheduler",
    "ScheduledTask",
    "TriggerManager",
    "Trigger",
    "TriggerType",
]
