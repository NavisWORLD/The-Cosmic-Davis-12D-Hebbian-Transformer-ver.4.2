"""
<<<<<<< HEAD:cosmos/infrastructure/__init__.py
cosmos Infrastructure Package
=======
Farnsworth Infrastructure Package
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/infrastructure/__init__.py

"Good news, everyone! I've automated infrastructure itself!"

Infrastructure as Code management with Terraform, Pulumi, and drift detection.
"""

<<<<<<< HEAD:cosmos/infrastructure/__init__.py
from cosmos.infrastructure.terraform_manager import (
=======
from farnsworth.infrastructure.terraform_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/infrastructure/__init__.py
    TerraformManager,
    TerraformState,
    TerraformPlan,
)
<<<<<<< HEAD:cosmos/infrastructure/__init__.py
from cosmos.infrastructure.drift_detector import (
=======
from farnsworth.infrastructure.drift_detector import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/infrastructure/__init__.py
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
