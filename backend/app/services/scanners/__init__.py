"""
Scanner plugins — vulnerability scanning via external tools.

Architecture:
    BaseScanner → NmapScanner, NucleiScanner, TrivyScanner
    ScannerFactory selects scanner(s) based on ScanType

Parsers (in parsers/ subpackage):
    NmapXMLParser, NucleiJSONParser, TrivyJSONParser
"""

from app.services.scanners.base import BaseScanner, RawFinding, ScannerFactory, ScannerError
from app.services.scanners.nmap_scanner import NmapScanner
from app.services.scanners.nuclei_scanner import NucleiScanner
from app.services.scanners.trivy_scanner import TrivyScanner

__all__ = [
    "BaseScanner",
    "RawFinding",
    "ScannerFactory",
    "ScannerError",
    "NmapScanner",
    "NucleiScanner",
    "TrivyScanner",
]
