"""
Heuristic Sigma rule tester: extracts string tokens from YAML detection and scores log lines.

Not a full Sigma engine; suitable for "does this rule touch these logs?" in the UI.
"""

from __future__ import annotations

import re
from typing import Any

import yaml


def _collect_strings(obj: Any, out: list[str], depth: int = 0) -> None:
    if depth > 20:
        return
    if isinstance(obj, str):
        s = obj.strip()
        if len(s) >= 3 and not s.startswith("${"):
            out.append(s)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("condition", "level", "status", "author", "description", "title", "references"):
                continue
            _collect_strings(v, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _collect_strings(item, out, depth + 1)


def extract_sigma_tokens(yaml_str: str) -> tuple[list[str], str | None]:
    """Return deduped match tokens and parse error if any."""
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        return [], str(e)
    if not isinstance(data, dict):
        return [], "YAML root must be a mapping"
    detection = data.get("detection")
    if detection is None:
        return [], "Missing detection: key"
    tokens: list[str] = []
    _collect_strings(detection, tokens)
    # Dedupe, prefer longer IOC-like strings
    seen: set[str] = set()
    uniq: list[str] = []
    for t in sorted(set(tokens), key=len, reverse=True):
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        uniq.append(t)
    return uniq[:40], None


def log_matches_tokens(log: str, tokens: list[str]) -> bool:
    if not tokens:
        return False
    low = log.lower()
    hits = sum(1 for t in tokens if t.lower() in low)
    need = 1 if len(tokens) <= 2 else min(2, len(tokens))
    return hits >= need


def test_sigma_against_logs(
    yaml_str: str, logs: list[str]
) -> tuple[int, list[int], list[str], str | None]:
    """Returns (match_count, matching_indices, token_preview, parse_error)."""
    tokens, err = extract_sigma_tokens(yaml_str)
    if err:
        return 0, [], [], err
    if not tokens:
        return 0, [], [], "no_tokens_extracted"
    indices = [i for i, log in enumerate(logs) if log_matches_tokens(log, tokens)]
    preview = tokens[:12]
    return len(indices), indices, preview, None
