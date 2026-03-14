"""
Prompt templates for AI-powered remediation and triage.

Design principles:
- Structured output request (Markdown with specific sections)
- Context-rich: include CVSS, EPSS, KEV data when available
- Role-specific: system prompt establishes expertise
- Actionable: demand concrete steps, not vague advice
"""

from typing import Any

from app.models.finding import Finding


REMEDIATION_SYSTEM_PROMPT = """\
You are a senior cybersecurity engineer specializing in vulnerability remediation.

Your task is to provide clear, actionable remediation guidance for the given vulnerability.

Rules:
- Structure your response in Markdown with these sections:
  ## Summary
  Brief description of the vulnerability and its impact.

  ## Risk Assessment
  Why this matters — consider CVSS, EPSS probability, and whether it's actively exploited.

  ## Remediation Steps
  Numbered, concrete steps to fix this vulnerability. Include:
  - Specific commands, configuration changes, or code modifications
  - Package versions to upgrade to (if applicable)
  - Configuration file paths and exact settings

  ## Verification
  How to verify the fix was applied successfully.

  ## References
  Relevant links (CVE database, vendor advisories, etc.)

- Be specific to the technology stack mentioned.
- If a patch/upgrade exists, prioritize that over workarounds.
- If the vulnerability is in a dependency, mention both direct fix and workaround.
- Keep the response concise but complete — aim for 300-500 words.
"""


TRIAGE_SYSTEM_PROMPT = """\
You are a security analyst performing vulnerability triage.

Analyze the provided vulnerability finding and determine:
1. Whether this is likely a TRUE POSITIVE or FALSE POSITIVE
2. The effective risk level considering the deployment context
3. Recommended priority: CRITICAL (fix now), HIGH (this sprint), MEDIUM (next sprint), LOW (backlog)

Structure your response as:
## Assessment
True/false positive determination with reasoning.

## Effective Risk
Context-adjusted risk considering EPSS data and CISA KEV status.

## Recommended Action
Concrete next step (patch, config change, accept risk, investigate further).
"""


def build_remediation_user_prompt(
    finding: Finding,
    vuln_context: dict[str, Any] | None = None,
) -> str:
    """
    Build the user prompt with full finding context for remediation.

    Includes all available enrichment data from the Vulnerability
    reference table for maximum LLM context.

    Args:
        finding: The Finding ORM object.
        vuln_context: Optional dict from RemediationEngine._get_vuln_context().

    Returns:
        Formatted user prompt string.
    """
    sections = []

    # Finding basics
    sections.append(f"**Vulnerability:** {finding.title}")
    sections.append(f"**Severity:** {finding.severity.value.upper()}")
    sections.append(f"**Description:** {finding.description}")

    if finding.scanner_name:
        sections.append(f"**Detected by:** {finding.scanner_name}")

    # CVE / CWE
    if finding.cve_id:
        sections.append(f"**CVE ID:** {finding.cve_id}")
    if finding.cwe_id:
        sections.append(f"**CWE ID:** {finding.cwe_id}")

    # CVSS scoring
    if finding.cvss_score is not None:
        sections.append(f"**CVSS v3.1 Score:** {finding.cvss_score}")
    if finding.cvss_vector:
        sections.append(f"**CVSS Vector:** {finding.cvss_vector}")

    # EPSS
    if finding.epss_score is not None:
        pct = finding.epss_score * 100
        sections.append(f"**EPSS Score:** {finding.epss_score:.4f} ({pct:.1f}% exploitation probability in 30 days)")
    if finding.epss_percentile is not None:
        sections.append(f"**EPSS Percentile:** {finding.epss_percentile:.2f}")

    # CISA KEV
    if finding.is_cisa_kev:
        sections.append("**CISA KEV:** YES — actively exploited in the wild")

    # Evidence (scanner-specific details)
    if finding.evidence:
        sections.append(f"**Scanner Evidence:** {finding.evidence}")

    # Enrichment from Vulnerability reference table
    if vuln_context:
        sections.append("")
        sections.append("--- Additional Context from NVD ---")
        if vuln_context.get("description"):
            sections.append(f"**NVD Description:** {vuln_context['description']}")
        if vuln_context.get("vendor"):
            sections.append(f"**Vendor:** {vuln_context['vendor']}")
        if vuln_context.get("product"):
            sections.append(f"**Product:** {vuln_context['product']}")
        if vuln_context.get("cwe_ids"):
            sections.append(f"**CWE IDs:** {vuln_context['cwe_ids']}")
        if vuln_context.get("kev_ransomware_use"):
            sections.append("**Ransomware Use:** Known use in ransomware campaigns")
        if vuln_context.get("kev_due_date"):
            sections.append(f"**CISA Remediation Deadline:** {vuln_context['kev_due_date']}")
        if vuln_context.get("references"):
            sections.append(f"**References:** {vuln_context['references']}")

    sections.append("")
    sections.append("Please provide detailed remediation guidance for this vulnerability.")

    return "\n".join(sections)


def build_triage_user_prompt(
    finding: Finding,
    vuln_context: dict[str, Any] | None = None,
) -> str:
    """
    Build the user prompt for AI-assisted triage.

    Args:
        finding: The Finding ORM object.
        vuln_context: Optional enrichment from Vulnerability table.

    Returns:
        Formatted user prompt for triage assessment.
    """
    sections = []

    sections.append(f"**Finding:** {finding.title}")
    sections.append(f"**Severity:** {finding.severity.value.upper()}")
    sections.append(f"**Scanner:** {finding.scanner_name or 'unknown'}")
    sections.append(f"**Description:** {finding.description}")

    if finding.cve_id:
        sections.append(f"**CVE:** {finding.cve_id}")

    if finding.cvss_score is not None:
        sections.append(f"**CVSS Score:** {finding.cvss_score}")

    if finding.epss_score is not None:
        pct = finding.epss_score * 100
        sections.append(f"**EPSS:** {finding.epss_score:.4f} ({pct:.1f}% chance of exploitation in 30 days)")

    if finding.is_cisa_kev:
        sections.append("**CISA KEV:** ACTIVELY EXPLOITED")

    if finding.risk_score is not None:
        sections.append(f"**Faust Risk Score:** {finding.risk_score}/100")

    if finding.evidence:
        sections.append(f"**Evidence:** {finding.evidence}")

    sections.append("")
    sections.append("Assess whether this is a true positive and recommend triage priority.")

    return "\n".join(sections)
