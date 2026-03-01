"""
<<<<<<< HEAD:cosmos/health/providers/__init__.py
cosmos Health Providers
=======
Farnsworth Health Providers
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/health/providers/__init__.py

Multi-provider health data integration supporting Apple Health, Fitbit, Oura, WHOOP, and more.
"""

from .base import HealthProvider, HealthProviderManager, OAuthCredentials
from .mock import MockHealthProvider
from .fitbit import FitbitProvider
from .oura import OuraProvider
from .whoop import WHOOPProvider
from .apple_health import AppleHealthProvider

__all__ = [
    "HealthProvider",
    "HealthProviderManager",
    "OAuthCredentials",
    "MockHealthProvider",
    "FitbitProvider",
    "OuraProvider",
    "WHOOPProvider",
    "AppleHealthProvider",
]
