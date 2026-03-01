"""
<<<<<<< HEAD:cosmos/compliance/__init__.py
cosmos Compliance and Audit Engine
=======
Farnsworth Compliance and Audit Engine
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/compliance/__init__.py

"The bureaucrats at the Central Bureaucracy are very particular about paperwork!"

Comprehensive compliance monitoring, audit logging, and policy enforcement.
"""

<<<<<<< HEAD:cosmos/compliance/__init__.py
from cosmos.compliance.compliance_engine import (
=======
from farnsworth.compliance.compliance_engine import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/compliance/__init__.py
    ComplianceEngine,
    CompliancePolicy,
    ComplianceCheck,
    ComplianceViolation,
    ComplianceStatus,
)
<<<<<<< HEAD:cosmos/compliance/__init__.py
from cosmos.compliance.audit_logger import (
=======
from farnsworth.compliance.audit_logger import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/compliance/__init__.py
    AuditLogger,
    AuditEvent,
    AuditEventType,
)
<<<<<<< HEAD:cosmos/compliance/__init__.py
from cosmos.compliance.policy_engine import (
=======
from farnsworth.compliance.policy_engine import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/compliance/__init__.py
    PolicyEngine,
    Policy,
    PolicyRule,
)

__all__ = [
    "ComplianceEngine",
    "CompliancePolicy",
    "ComplianceCheck",
    "ComplianceViolation",
    "ComplianceStatus",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "PolicyEngine",
    "Policy",
    "PolicyRule",
]
