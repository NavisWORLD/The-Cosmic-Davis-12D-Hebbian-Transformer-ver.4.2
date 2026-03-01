"""
<<<<<<< HEAD:cosmos/integration/cloud/__init__.py
cosmos Cloud Integration Package
=======
Farnsworth Cloud Integration Package
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/cloud/__init__.py

"Good news, everyone! I can manage all your clouds from one place!"

Comprehensive cloud provider integrations for Azure, AWS, GCP.
"""

<<<<<<< HEAD:cosmos/integration/cloud/__init__.py
from cosmos.integration.cloud.azure_manager import (
    AzureManager,
    azure_manager,
)
from cosmos.integration.cloud.aws_manager import (
=======
from farnsworth.integration.cloud.azure_manager import (
    AzureManager,
    azure_manager,
)
from farnsworth.integration.cloud.aws_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/cloud/__init__.py
    AWSManager,
    aws_manager,
)


__all__ = [
    "AzureManager",
    "azure_manager",
    "AWSManager",
    "aws_manager",
]
