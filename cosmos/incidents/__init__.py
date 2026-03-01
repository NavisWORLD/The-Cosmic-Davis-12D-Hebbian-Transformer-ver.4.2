"""
<<<<<<< HEAD:cosmos/incidents/__init__.py
cosmos Incident Response and Runbook System
=======
Farnsworth Incident Response and Runbook System
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/incidents/__init__.py

"When things go wrong, which they often do in my lab,
 it's best to have a plan... or at least a good excuse!"

Comprehensive incident management with automated runbooks.
"""

<<<<<<< HEAD:cosmos/incidents/__init__.py
from cosmos.incidents.incident_manager import (
=======
from farnsworth.incidents.incident_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/incidents/__init__.py
    IncidentManager,
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
<<<<<<< HEAD:cosmos/incidents/__init__.py
from cosmos.incidents.runbook_executor import (
=======
from farnsworth.incidents.runbook_executor import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/incidents/__init__.py
    RunbookExecutor,
    Runbook,
    RunbookStep,
    RunbookExecution,
)
<<<<<<< HEAD:cosmos/incidents/__init__.py
from cosmos.incidents.pagerduty_integration import PagerDutyIntegration
from cosmos.incidents.opsgenie_integration import OpsGenieIntegration
=======
from farnsworth.incidents.pagerduty_integration import PagerDutyIntegration
from farnsworth.incidents.opsgenie_integration import OpsGenieIntegration
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/incidents/__init__.py

__all__ = [
    "IncidentManager",
    "Incident",
    "IncidentSeverity",
    "IncidentStatus",
    "RunbookExecutor",
    "Runbook",
    "RunbookStep",
    "RunbookExecution",
    "PagerDutyIntegration",
    "OpsGenieIntegration",
]
