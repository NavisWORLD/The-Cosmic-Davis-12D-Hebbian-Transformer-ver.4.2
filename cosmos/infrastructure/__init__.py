"""
cosmos Infrastructure Package

"Good news, everyone! I've automated infrastructure itself!"

Infrastructure as Code management with Terraform, Pulumi, and drift detection.
"""

from cosmos.infrastructure.terraform_manager import (
    TerraformManager,
    TerraformState,
    TerraformPlan,
)
from cosmos.infrastructure.drift_detector import (
    DriftDetector,
    DriftReport,
)

__all__ = [
    "TerraformManager",
    "TerraformState",
    "TerraformPlan",
    "DriftDetector",
    "DriftReport",
]
