"""
cosmos Security Tools

"Good news, everyone! I've built security tools for responsible researchers!"

Comprehensive offensive and defensive security toolkit for authorized testing.
"""

from cosmos.tools.security.vulnerability_scanner import (
    VulnerabilityScanner,
    VulnerabilityReport,
    vulnerability_scanner,
)
from cosmos.tools.security.threat_analyzer import (
    ThreatAnalyzer,
    ThreatIndicator,
    threat_analyzer,
)
from cosmos.tools.security.forensics import (
    ForensicsToolkit,
    forensics_toolkit,
)
from cosmos.tools.security.header_analyzer import (
    HeaderAnalyzer,
    EmailHeaderAnalysis,
    header_analyzer,
)
from cosmos.tools.security.recon import (
    ReconEngine,
    ReconResult,
    recon_engine,
)
from cosmos.tools.security.edr import (
    EDREngine,
    SecurityAlert,
    DetectionRule,
    edr_engine,
)
from cosmos.tools.security.log_parser import (
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
