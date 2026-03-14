"""
Nmap XML output parser.

Parses nmap's XML output format (-oX) into RawFinding objects.

Nmap XML structure (relevant parts):
    <nmaprun>
        <host>
            <address addr="192.168.1.1" addrtype="ipv4"/>
            <hostnames>
                <hostname name="router.local" type="PTR"/>
            </hostnames>
            <ports>
                <port protocol="tcp" portid="22">
                    <state state="open"/>
                    <service name="ssh" product="OpenSSH" version="8.9p1"
                             extrainfo="Ubuntu Linux" ostype="Linux"/>
                    <script id="vulners" output="...">
                        <table>
                            <elem key="id">CVE-2023-38408</elem>
                            <elem key="cvss">9.8</elem>
                            <elem key="type">cve</elem>
                        </table>
                    </script>
                </port>
            </ports>
            <os>
                <osmatch name="Linux 5.4" accuracy="95"/>
            </os>
        </host>
    </nmaprun>

BUILDER: implement the parse() method following the architecture below.
Use xml.etree.ElementTree (stdlib) — do NOT use lxml (extra dependency).
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any

from app.services.scanners.base import RawFinding

logger = logging.getLogger(__name__)


class NmapXMLParser:
    """
    Converts nmap XML output into a list of RawFinding objects.

    Finding types produced:
    1. OPEN PORT — one finding per open port with service info
    2. NSE VULN — one finding per NSE script result that identifies a CVE
    3. OS DETECTION — one informational finding per host with OS fingerprint
    """

    def __init__(self, scanner_name: str = "nmap"):
        self.scanner_name = scanner_name

    def parse(self, xml_output: str) -> list[RawFinding]:
        """
        Parse nmap XML output into RawFinding objects.

        Args:
            xml_output: Raw nmap XML string.

        Returns:
            List of RawFinding objects (open port findings + NSE vuln findings + OS findings).
        """
        findings: list[RawFinding] = []

        if not xml_output or not xml_output.strip():
            logger.warning("NmapXMLParser received empty output")
            return findings

        try:
            root = ET.fromstring(xml_output)
        except ET.ParseError as e:
            logger.error("Failed to parse nmap XML: %s", e)
            return findings

        for host_elem in root.findall("host"):
            # Skip hosts that are not up
            status = host_elem.find("status")
            if status is not None and status.get("state") != "up":
                continue

            addr = self._extract_address(host_elem)
            hostname = self._extract_hostname(host_elem)
            identifier = hostname or addr  # prefer hostname for readability

            # Parse open ports and NSE scripts
            for port_elem in host_elem.findall(".//port"):
                findings.extend(self._parse_port(port_elem, identifier, addr))

            # Parse OS detection
            os_finding = self._parse_os(host_elem, identifier)
            if os_finding:
                findings.append(os_finding)

        logger.info("NmapXMLParser parsed %d findings from XML output", len(findings))
        return findings

    def _extract_address(self, host_elem: ET.Element) -> str:
        """
        Extract IP address from host element.

        Look for <address addr="..." addrtype="ipv4|ipv6"/>.
        Prefer ipv4 over ipv6. Return first found.
        """
        for addr_elem in host_elem.findall("address"):
            if addr_elem.get("addrtype") in ("ipv4", "ipv6"):
                return addr_elem.get("addr", "unknown")
        return "unknown"

    def _extract_hostname(self, host_elem: ET.Element) -> str | None:
        """Extract first hostname from <hostnames><hostname name="..."/>."""
        hostname_elem = host_elem.find(".//hostname")
        if hostname_elem is not None:
            return hostname_elem.get("name")
        return None

    def _parse_port(
        self,
        port_elem: ET.Element,
        identifier: str,
        ip_address: str,
    ) -> list[RawFinding]:
        """Parse a single <port> element into finding(s)."""
        findings: list[RawFinding] = []

        # Only process open ports
        state_elem = port_elem.find("state")
        if state_elem is None or state_elem.get("state") != "open":
            return findings

        port = int(port_elem.get("portid", 0))
        protocol = port_elem.get("protocol", "tcp")

        # Extract service info
        service_elem = port_elem.find("service")
        service_name = "unknown"
        product = ""
        version = ""
        extra_info = ""
        if service_elem is not None:
            service_name = service_elem.get("name", "unknown")
            product = service_elem.get("product", "")
            version = service_elem.get("version", "")
            extra_info = service_elem.get("extrainfo", "")

        # Apply port risk heuristic
        HIGH_RISK_PORTS = {21, 23, 445, 3389, 5900, 1433, 3306, 27017}
        INFO_PORTS = {80, 443, 22, 53, 8080, 8443}
        if port in HIGH_RISK_PORTS:
            severity = "medium"
        elif port in INFO_PORTS:
            severity = "info"
        else:
            severity = "low"

        banner = " ".join(filter(None, [product, version, extra_info])).strip()
        service_display = service_name if not banner else f"{service_name} ({banner})"

        port_finding = RawFinding(
            title=f"Open Port {port}/{protocol} ({service_display})",
            description=(
                f"Port {port}/{protocol} is open running {service_display}. "
                f"Host: {identifier} ({ip_address})."
            ),
            severity=severity,
            asset_identifier=identifier,
            scanner_name=self.scanner_name,
            scanner_rule_id=f"nmap:open-port:{port}",
            port=port,
            protocol=protocol,
            service_name=service_name,
            service_version=version,
            evidence={
                "port": port,
                "protocol": protocol,
                "service": service_name,
                "product": product,
                "version": version,
                "extrainfo": extra_info,
                "ip_address": ip_address,
            },
        )
        findings.append(port_finding)

        # Parse NSE script results for CVE-level findings
        for script_elem in port_elem.findall("script"):
            vuln_findings = self._parse_nse_script(
                script_elem, identifier, port, protocol, service_name
            )
            findings.extend(vuln_findings)

        return findings

    def _parse_nse_script(
        self,
        script_elem: ET.Element,
        identifier: str,
        port: int,
        protocol: str,
        service_name: str,
    ) -> list[RawFinding]:
        """Parse an NSE script result into vulnerability findings."""
        findings: list[RawFinding] = []
        script_id = script_elem.get("id", "")
        script_output = script_elem.get("output", "")

        # Handle the "vulners" NSE script — returns table of CVEs with scores
        if script_id == "vulners":
            for table_elem in script_elem.findall(".//table"):
                cve_id: str | None = None
                cvss_score: float | None = None
                entry_type: str | None = None

                for elem_elem in table_elem.findall("elem"):
                    key = elem_elem.get("key", "")
                    val = elem_elem.text or ""
                    if key == "id":
                        cve_id = val.strip()
                    elif key == "cvss":
                        try:
                            cvss_score = float(val)
                        except ValueError:
                            pass
                    elif key == "type":
                        entry_type = val.strip().lower()

                if cve_id and entry_type == "cve":
                    sev = self._severity_from_cvss(cvss_score) if cvss_score else "medium"
                    findings.append(RawFinding(
                        title=f"{cve_id} — {service_name} on port {port}/{protocol}",
                        description=(
                            f"NSE vulners script detected {cve_id} on {service_name} "
                            f"(port {port}/{protocol}) at {identifier}. "
                            f"NSE output: {script_output[:500]}"
                        ),
                        severity=sev,
                        asset_identifier=identifier,
                        cve_id=cve_id,
                        cvss_score=cvss_score,
                        scanner_name=self.scanner_name,
                        scanner_rule_id=f"nse:vulners:{cve_id}",
                        port=port,
                        protocol=protocol,
                        service_name=service_name,
                        evidence={
                            "script_id": script_id,
                            "port": port,
                            "service": service_name,
                            "script_output": script_output[:1000],
                        },
                    ))

        # Handle generic vuln/http-vuln-*/smb-vuln-*/ssl-* scripts
        elif (
            script_id == "vuln"
            or script_id.startswith("http-vuln-")
            or script_id.startswith("smb-vuln-")
            or script_id.startswith("ssl-")
            or script_id.startswith("ftp-vuln-")
        ):
            if "VULNERABLE" in script_output.upper() or "CVE" in script_output.upper():
                # Extract CVE from output if present
                import re
                cve_matches = re.findall(r"CVE-\d{4}-\d{4,7}", script_output)
                cve_id = cve_matches[0] if cve_matches else None

                findings.append(RawFinding(
                    title=f"{script_id} — {service_name} on port {port}/{protocol}",
                    description=(
                        f"NSE script '{script_id}' detected a vulnerability on "
                        f"{service_name} (port {port}/{protocol}) at {identifier}.\n"
                        f"Output: {script_output[:1000]}"
                    ),
                    severity="high",  # Conservative: mark these as high without CVSS
                    asset_identifier=identifier,
                    cve_id=cve_id,
                    scanner_name=self.scanner_name,
                    scanner_rule_id=f"nse:{script_id}:{cve_id or 'generic'}",
                    port=port,
                    protocol=protocol,
                    service_name=service_name,
                    evidence={
                        "script_id": script_id,
                        "port": port,
                        "service": service_name,
                        "script_output": script_output[:2000],
                    },
                ))

        return findings

    def _parse_os(self, host_elem: ET.Element, identifier: str) -> RawFinding | None:
        """Parse OS detection results into an informational finding (accuracy >= 80% only)."""
        os_elem = host_elem.find("os")
        if os_elem is None:
            return None

        osmatch = os_elem.find("osmatch")
        if osmatch is None:
            return None

        os_name = osmatch.get("name", "Unknown OS")
        accuracy_str = osmatch.get("accuracy", "0")
        try:
            accuracy = int(accuracy_str)
        except ValueError:
            return None

        if accuracy < 80:
            return None

        # Extract OS family from osclass if available
        os_family = ""
        osclass = os_elem.find(".//osclass")
        if osclass is not None:
            os_family = osclass.get("osfamily", "")

        return RawFinding(
            title=f"OS Detected: {os_name}",
            description=(
                f"Nmap OS fingerprinting identified the operating system on {identifier} "
                f"as '{os_name}' with {accuracy}% confidence."
            ),
            severity="info",
            asset_identifier=identifier,
            scanner_name=self.scanner_name,
            scanner_rule_id="nmap:os-detection",
            evidence={
                "os_name": os_name,
                "accuracy": accuracy,
                "os_family": os_family,
            },
        )

    @staticmethod
    def _severity_from_cvss(cvss_score: float) -> str:
        """Map CVSS score to severity string per CVSS v3.1 spec."""
        if cvss_score >= 9.0:
            return "critical"
        elif cvss_score >= 7.0:
            return "high"
        elif cvss_score >= 4.0:
            return "medium"
        elif cvss_score >= 0.1:
            return "low"
        return "info"
