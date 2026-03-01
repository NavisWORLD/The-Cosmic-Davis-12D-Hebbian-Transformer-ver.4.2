"""
<<<<<<< HEAD:cosmos/secrets/__init__.py
cosmos Secrets and Credentials Vault
=======
Farnsworth Secrets and Credentials Vault
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/secrets/__init__.py

"I've hidden my most dangerous inventions in a vault...
 but I can never remember the combination!"

Multi-provider secrets management with rotation and audit logging.
"""

<<<<<<< HEAD:cosmos/secrets/__init__.py
from cosmos.secrets.vault_manager import (
=======
from farnsworth.secrets.vault_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/secrets/__init__.py
    VaultManager,
    Secret,
    SecretVersion,
    SecretType,
)
<<<<<<< HEAD:cosmos/secrets/__init__.py
from cosmos.secrets.hashicorp_vault import HashiCorpVaultProvider
from cosmos.secrets.aws_secrets import AWSSecretsProvider
from cosmos.secrets.azure_keyvault import AzureKeyVaultProvider
=======
from farnsworth.secrets.hashicorp_vault import HashiCorpVaultProvider
from farnsworth.secrets.aws_secrets import AWSSecretsProvider
from farnsworth.secrets.azure_keyvault import AzureKeyVaultProvider
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/secrets/__init__.py

__all__ = [
    "VaultManager",
    "Secret",
    "SecretVersion",
    "SecretType",
    "HashiCorpVaultProvider",
    "AWSSecretsProvider",
    "AzureKeyVaultProvider",
]
