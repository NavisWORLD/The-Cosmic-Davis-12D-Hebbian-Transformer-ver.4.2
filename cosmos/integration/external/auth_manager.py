"""
<<<<<<< HEAD:cosmos/integration/external/auth_manager.py
cosmos Authentication Manager.
=======
Farnsworth Authentication Manager.
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/external/auth_manager.py

Manages secure storage and interactive retrieval of credentials for external integrations.
Uses the system keyring service for security.
"""

import os
import getpass
from typing import Dict, Optional
from loguru import logger

# Try to import keyring, fallback to environment variables/file if not available
try:
    import keyring
except ImportError:
    keyring = None
    logger.warning("Keyring not installed. Credentials will be stored in environment variables only.")

class AuthManager:
<<<<<<< HEAD:cosmos/integration/external/auth_manager.py
    def __init__(self, service_prefix: str = "cosmos_integration"):
=======
    def __init__(self, service_prefix: str = "farnsworth_integration"):
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/external/auth_manager.py
        self.prefix = service_prefix

    def get_credential(self, provider_name: str, key_name: str = "api_key") -> Optional[str]:
        """
        Retrieve a credential. 
        Priority:
<<<<<<< HEAD:cosmos/integration/external/auth_manager.py
        1. Environment Variable (cosmos_{PROVIDER}_{KEY})
        2. System Keyring
        """
        env_var = f"cosmos_{provider_name.upper()}_{key_name.upper()}"
=======
        1. Environment Variable (FARNSWORTH_{PROVIDER}_{KEY})
        2. System Keyring
        """
        env_var = f"FARNSWORTH_{provider_name.upper()}_{key_name.upper()}"
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/external/auth_manager.py
        val = os.environ.get(env_var)
        if val:
            return val
            
        if keyring:
            try:
                val = keyring.get_password(f"{self.prefix}_{provider_name}", key_name)
                if val:
                    return val
            except Exception as e:
                logger.warning(f"Keyring lookup failed: {e}")
                
        return None

    def store_credential(self, provider_name: str, key_name: str, value: str):
        """Securely store a credential."""
        if keyring:
            try:
                keyring.set_password(f"{self.prefix}_{provider_name}", key_name, value)
                logger.info(f"Stored credential for {provider_name}/{key_name} in system keyring.")
            except Exception as e:
                logger.error(f"Failed to store credential in keyring: {e}")
                # Fallbback? No, don't write secrets to disk in plain text.

    def request_setup(self, provider_name: str, required_keys: list[str]) -> Dict[str, str]:
        """
        Interactive setup wizard for a provider.
        """
        creds = {}
        print(f"\n🔌 Setup for {provider_name} Integration")
        print("----------------------------------------")
        
        for key in required_keys:
            current = self.get_credential(provider_name, key)
            if current:
                use_existing = input(f"Found existing {key}. Use it? [Y/n]: ").lower()
                if use_existing != 'n':
                    creds[key] = current
                    continue
            
            val = getpass.getpass(f"Enter {key}: ")
            if val.strip():
                self.store_credential(provider_name, key, val)
                creds[key] = val
            else:
                logger.warning(f"Skipping empty {key}")
                
        return creds

auth_manager = AuthManager()
