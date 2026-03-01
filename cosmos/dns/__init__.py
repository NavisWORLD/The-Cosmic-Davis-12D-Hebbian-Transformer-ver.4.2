"""
<<<<<<< HEAD:cosmos/dns/__init__.py
cosmos DNS Management Package
=======
Farnsworth DNS Management Package
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/dns/__init__.py

"Good news, everyone! I can now control the very fabric of the internet!"

Multi-provider DNS management including MX records and SSL certificates.
"""

<<<<<<< HEAD:cosmos/dns/__init__.py
from cosmos.dns.dns_manager import (
=======
from farnsworth.dns.dns_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/dns/__init__.py
    DNSManager,
    DNSRecord,
    DNSRecordType,
)
<<<<<<< HEAD:cosmos/dns/__init__.py
from cosmos.dns.ssl_certificates import (
=======
from farnsworth.dns.ssl_certificates import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/dns/__init__.py
    SSLManager,
    Certificate,
)

__all__ = [
    "DNSManager",
    "DNSRecord",
    "DNSRecordType",
    "SSLManager",
    "Certificate",
]
