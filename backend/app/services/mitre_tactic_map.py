"""Map MITRE technique IDs to Enterprise tactic names for attack-chain visualization."""

from __future__ import annotations

# Base technique ID (strip sub-technique) -> ATT&CK tactic
_TECH_BASE_TO_TACTIC: dict[str, str] = {
    "T1003": "Credential Access",
    "T1005": "Collection",
    "T1021": "Lateral Movement",
    "T1027": "Defense Evasion",
    "T1036": "Defense Evasion",
    "T1047": "Execution",
    "T1053": "Execution",
    "T1055": "Defense Evasion",
    "T1059": "Execution",
    "T1071": "Command and Control",
    "T1078": "Defense Evasion",
    "T1098": "Persistence",
    "T1105": "Command and Control",
    "T1106": "Execution",
    "T1110": "Credential Access",
    "T1133": "Initial Access",
    "T1190": "Initial Access",
    "T1204": "Execution",
    "T1218": "Defense Evasion",
    "T1486": "Impact",
    "T1530": "Collection",
    "T1566": "Initial Access",
    "T1568": "Command and Control",
    "T1595": "Reconnaissance",
    "T1621": "Credential Access",
    "T1657": "Impact",
    "T0855": "Impair Process Control",
    "T0806": "Impair Process Control",
    "T0865": "Command and Control",
}


def tactic_for_technique(technique_id: str) -> str:
    tid = technique_id.strip().upper()
    if tid in _TECH_BASE_TO_TACTIC:
        return _TECH_BASE_TO_TACTIC[tid]
    base = tid.split(".")[0]
    return _TECH_BASE_TO_TACTIC.get(base, "Execution")


# Ordered tactics for stable layer layout (subset of Enterprise + OT)
TACTIC_ORDER: list[str] = [
    "Reconnaissance",
    "Initial Access",
    "Execution",
    "Persistence",
    "Privilege Escalation",
    "Defense Evasion",
    "Credential Access",
    "Discovery",
    "Lateral Movement",
    "Collection",
    "Command and Control",
    "Exfiltration",
    "Impact",
    "Impair Process Control",
]
