"""Regex + NER-assisted IOC extraction."""

from __future__ import annotations

import re

from app.schemas import IOC

_IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)
# Simplified IPv6
_IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,}[0-9a-fA-F:]{1,}\b")
_MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Windows path or simple unix path token
_PATH = re.compile(
    r'\b(?:[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]+|/(?:[\w.-]+/)+[\w.-]+)\b'
)
_USER = re.compile(r"\b(?:user|duser|suser|SubjectUserName|username)[:=]\s*([^\s|,]+)", re.I)
_DOMAIN_LIKE = re.compile(
    r"\b(?:qname|host|hostname|deviceHostName|dst|src)[:=]\s*([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)\b",
    re.I,
)
_URL = re.compile(r"https?://[^\s\"'<>|]+", re.I)


def _dedupe_iocs(items: list[IOC]) -> list[IOC]:
    seen: set[tuple[str, str]] = set()
    out: list[IOC] = []
    for i in items:
        key = (i.type, i.value.strip())
        if key in seen or not key[1]:
            continue
        seen.add(key)
        out.append(i)
    return out


def extract_iocs_from_text(text: str) -> list[IOC]:
    found: list[IOC] = []
    for m in _IPV4.finditer(text):
        found.append(IOC(type="ip", value=m.group(0), context="ipv4"))
    for m in _IPV6.finditer(text):
        found.append(IOC(type="ip", value=m.group(0), context="ipv6"))
    for m in _URL.finditer(text):
        u = m.group(0).rstrip(").,;")
        found.append(IOC(type="url", value=u, context="url"))
    for m in _MD5.finditer(text):
        found.append(IOC(type="hash", value=m.group(0), context="md5"))
    for m in _SHA256.finditer(text):
        found.append(IOC(type="hash", value=m.group(0), context="sha256"))
    for m in _EMAIL.finditer(text):
        found.append(IOC(type="email", value=m.group(0), context="email"))
    for m in _PATH.finditer(text):
        found.append(IOC(type="file", value=m.group(0), context="path"))
    for m in _USER.finditer(text):
        found.append(IOC(type="user", value=m.group(1).strip("\\"), context="log field"))
    for m in _DOMAIN_LIKE.finditer(text):
        val = m.group(1)
        if not _IPV4.fullmatch(val):
            # Skip if looks like URL host already captured
            if "://" not in val:
                found.append(IOC(type="domain", value=val.lower(), context=m.group(0)[:80]))

    # Hostnames in JSON-ish strings
    for m in re.finditer(r'"host(?:name)?"\s*:\s*"([^"]+)"', text, re.I):
        found.append(IOC(type="domain", value=m.group(1), context="json host"))

    return _dedupe_iocs(found)


def merge_ner_entities(text: str, ner_groups: list[dict]) -> list[IOC]:
    """Map HF token-classification groups to IOC list."""
    out: list[IOC] = []
    for g in ner_groups:
        entity = (g.get("entity_group") or g.get("entity") or "").upper()
        word = (g.get("word") or "").replace("##", "").strip()
        if not word:
            continue
        if entity in ("MALWARE", "THREAT", "ATTACK", "IOC"):
            out.append(IOC(type="other", value=word, context=f"ner:{entity}"))
        elif entity in ("IP", "IP_ADDRESS"):
            out.append(IOC(type="ip", value=word, context="ner"))
        elif entity in ("URL",):
            out.append(IOC(type="url", value=word, context="ner"))
        elif entity in ("DOMAIN", "HOST"):
            out.append(IOC(type="domain", value=word.lower(), context="ner"))
        elif entity in ("HASH",):
            out.append(IOC(type="hash", value=word, context="ner"))
        elif entity in ("USER", "PERSON"):
            out.append(IOC(type="user", value=word, context="ner"))
    return _dedupe_iocs(out + extract_iocs_from_text(text))
