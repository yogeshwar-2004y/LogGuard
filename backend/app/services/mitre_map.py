"""Keyword → MITRE ATT&CK technique mapping (heuristic layer on top of ML)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import MitreTechnique

_BASE = "https://attack.mitre.org/techniques"


@dataclass(frozen=True)
class _Rule:
    pattern: re.Pattern[str]
    tid: str
    name: str


_RULES: list[_Rule] = [
    _Rule(re.compile(r"powershell|encodedcommand|-enc\b", re.I), "T1059", "Command and Scripting Interpreter"),
    _Rule(re.compile(r"lsass|mimikatz|procdump|sekurlsa", re.I), "T1003", "OS Credential Dumping"),
    _Rule(re.compile(r"rdp|terminal services|3389", re.I), "T1021", "Remote Services"),
    _Rule(re.compile(r"ssh.*fail|failed password|brute", re.I), "T1110", "Brute Force"),
    _Rule(re.compile(r"dns|beacon|dga", re.I), "T1071", "Application Layer Protocol"),
    _Rule(re.compile(r"putuserpolicy|iam\.|AssumeRole|CreateAccessKey", re.I), "T1098", "Account Manipulation"),
    _Rule(re.compile(r"mfa|otp|prompt_sent", re.I), "T1621", "Multi-Factor Authentication Request Generation"),
    _Rule(re.compile(r"modbus|scada|plc|holding_register", re.I), "T0855", "Unauthorized Command Message"),
    _Rule(re.compile(r"lateral|psexec|wmic.*process", re.I), "T1021", "Remote Services"),
    _Rule(re.compile(r"ransom|encrypt|\.locked|bitcoin", re.I), "T1486", "Data Encrypted for Impact"),
    _Rule(re.compile(r"bulk_export|ehr|phi|mrn", re.I), "T1530", "Data from Cloud Storage"),
    _Rule(re.compile(r"swift|wire transfer|fraud", re.I), "T1657", "Financial Theft"),
]


def _url_for_technique(tid: str) -> str:
    # T1059 -> enterprise/T1059
    return f"{_BASE}/{tid}"


def map_keywords_to_mitre(text: str, hints: list[str] | None = None) -> list[MitreTechnique]:
    seen: dict[str, float] = {}
    lower = text.lower()
    for rule in _RULES:
        if rule.pattern.search(text):
            seen[rule.tid] = max(seen.get(rule.tid, 0.0), 0.72)
    if hints:
        for h in hints:
            tid = h.strip().upper()
            if re.match(r"^T\d{4}(\.\d{3})?$", tid):
                seen[tid] = max(seen.get(tid, 0.0), 0.85)
    # Name lookup for hinted IDs only in rules + generic
    name_by_id = {r.tid: r.name for r in _RULES}
    out: list[MitreTechnique] = []
    for tid, conf in sorted(seen.items(), key=lambda x: -x[1]):
        name = name_by_id.get(tid, tid)
        out.append(MitreTechnique(id=tid, name=name, url=_url_for_technique(tid), confidence=round(conf, 3)))
    return out[:12]
