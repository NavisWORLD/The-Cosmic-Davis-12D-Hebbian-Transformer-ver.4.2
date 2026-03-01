"""
<<<<<<< HEAD:cosmos/tools/security/__init__.py
cosmos Security Tools
=======
Farnsworth Security Tools
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py

"Good news, everyone! I've built security tools for responsible researchers!"

Comprehensive offensive and defensive security toolkit for authorized testing.
"""

<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.vulnerability_scanner import (
=======
from farnsworth.tools.security.vulnerability_scanner import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    VulnerabilityScanner,
    VulnerabilityReport,
    vulnerability_scanner,
)
<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.threat_analyzer import (
=======
from farnsworth.tools.security.threat_analyzer import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    ThreatAnalyzer,
    ThreatIndicator,
    threat_analyzer,
)
<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.forensics import (
    ForensicsToolkit,
    forensics_toolkit,
)
from cosmos.tools.security.header_analyzer import (
=======
from farnsworth.tools.security.forensics import (
    ForensicsToolkit,
    forensics_toolkit,
)
from farnsworth.tools.security.header_analyzer import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    HeaderAnalyzer,
    EmailHeaderAnalysis,
    header_analyzer,
)
<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.recon import (
=======
from farnsworth.tools.security.recon import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    ReconEngine,
    ReconResult,
    recon_engine,
)
<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.edr import (
=======
from farnsworth.tools.security.edr import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    EDREngine,
    SecurityAlert,
    DetectionRule,
    edr_engine,
)
<<<<<<< HEAD:cosmos/tools/security/__init__.py
from cosmos.tools.security.log_parser import (
=======
from farnsworth.tools.security.log_parser import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/security/__init__.py
    SecurityLogParser,
    ParsedLogEntry,
    LogAnalysisReport,
    security_log_parser,
)


__all__ = [
    # Vulnerability Scanner
    "VulnerabilityScanner",
    "VulnerabilityReport",
    "vulnerability_scanner",
    # Threat Analyzer
    "ThreatAnalyzer",
    "ThreatIndicator",
    "threat_analyzer",
    # Forensics
    "ForensicsToolkit",
    "forensics_toolkit",
    # Header Analyzer
    "HeaderAnalyzer",
    "EmailHeaderAnalysis",
    "header_analyzer",
    # Recon Engine
    "ReconEngine",
    "ReconResult",
    "recon_engine",
    # EDR
    "EDREngine",
    "SecurityAlert",
    "DetectionRule",
    "edr_engine",
    # Log Parser
    "SecurityLogParser",
    "ParsedLogEntry",
    "LogAnalysisReport",
    "security_log_parser",
]
