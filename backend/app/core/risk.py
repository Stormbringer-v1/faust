"""
Faust composite risk scoring algorithm.

Combines CVSS base score, EPSS exploitation probability, and CISA KEV
status into a single 0–100 priority score for vulnerability triage.

Formula rationale:
- CVSS (50% weight): theoretical impact and exploitability
- EPSS (30% weight): real-world exploitation probability (30-day window)
- CISA KEV (20% weight): confirmed active exploitation in the wild

This produces a prioritized ranking that is significantly better than
raw CVSS alone — see Cyentia Institute research on EPSS effectiveness.
"""


def compute_risk_score(
    cvss_score: float | None = None,
    epss_score: float | None = None,
    is_cisa_kev: bool = False,
) -> float:
    """
    Compute Faust composite risk score (0–100).

    Args:
        cvss_score: CVSS v3.1 base score (0.0–10.0). None treated as 0.
        epss_score: EPSS probability (0.0–1.0). None treated as 0.
        is_cisa_kev: Whether CVE is in CISA Known Exploited Vulns catalog.

    Returns:
        Composite risk score rounded to one decimal place.

    Examples:
        >>> compute_risk_score(cvss_score=10.0, epss_score=1.0, is_cisa_kev=True)
        100.0
        >>> compute_risk_score(cvss_score=9.8, epss_score=0.97, is_cisa_kev=True)
        98.1
        >>> compute_risk_score(cvss_score=5.0, epss_score=0.1, is_cisa_kev=False)
        28.0
        >>> compute_risk_score(cvss_score=3.0, epss_score=0.01)
        15.3
        >>> compute_risk_score()
        0.0
    """
    cvss_component = ((cvss_score or 0.0) / 10.0) * 50.0
    epss_component = (epss_score or 0.0) * 30.0
    kev_component = 20.0 if is_cisa_kev else 0.0

    return min(100.0, round(cvss_component + epss_component + kev_component, 1))


def severity_from_risk_score(risk_score: float) -> str:
    """
    Map Faust risk score to a severity label for prioritization.

    Thresholds:
        90–100: CRITICAL — immediate remediation required
        70–89:  HIGH     — remediate within 1 sprint
        40–69:  MEDIUM   — plan remediation
        15–39:  LOW      — accept or backlog
        0–14:   INFO     — informational only
    """
    if risk_score >= 90.0:
        return "critical"
    elif risk_score >= 70.0:
        return "high"
    elif risk_score >= 40.0:
        return "medium"
    elif risk_score >= 15.0:
        return "low"
    else:
        return "info"
