"""
Token / span highlighting for the UI heatmap.

True SHAP over remote HF models is not available; we approximate using:
- NER entity spans (when the tokenizer returns offsets; else reconstruct)
- Regex IOC spans
- Keyword saliency vs a small cyber lexicon
"""

from __future__ import annotations

import re

from app.schemas import TokenHighlight

_CYBER_KEYWORDS = [
    "failed",
    "password",
    "powershell",
    "encoded",
    "ransom",
    "encrypt",
    "exfil",
    "mimikatz",
    "lsass",
    "rdp",
    "ssh",
    "brute",
    "policy",
    "assumeRole",
    "PutUser",
    "modbus",
    "plc",
    "beacon",
    "curl",
    "bulk_export",
    "mfa",
]


def _add_span(spans: list[tuple[int, int, float, str | None]], start: int, end: int, score: float, label: str | None):
    if start < 0 or end <= start:
        return
    spans.append((start, end, min(1.0, score), label))


def _merge_spans(spans: list[tuple[int, int, float, str | None]]) -> list[TokenHighlight]:
    if not spans:
        return []
    spans.sort(key=lambda x: (x[0], -x[2]))
    merged: list[TokenHighlight] = []
    for s, e, sc, lab in spans:
        overlap = False
        for m in merged:
            if not (e <= m.start or s >= m.end):
                overlap = True
                if sc > m.score:
                    m.score = sc
                    if lab:
                        m.label = lab
                break
        if not overlap:
            merged.append(TokenHighlight(start=s, end=e, score=sc, label=lab))
    merged.sort(key=lambda x: x.start)
    return merged


def build_highlights(
    text: str,
    ner_raw: list[dict] | None = None,
) -> list[TokenHighlight]:
    spans: list[tuple[int, int, float, str | None]] = []

    # Keyword hits
    for kw in _CYBER_KEYWORDS:
        for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
            _add_span(spans, m.start(), m.end(), 0.45, f"keyword:{kw}")

    # Simple “token” split heat: long base64-like strings
    for m in re.finditer(r"[A-Za-z0-9+/]{40,}={0,2}", text):
        _add_span(spans, m.start(), m.end(), 0.78, "high_entropy")

    # NER groups from HF often include start/end in newer API; else approximate by search
    if ner_raw:
        for ent in ner_raw:
            word = (ent.get("word") or "").replace("##", " ").strip()
            if len(word) < 2:
                continue
            eg = ent.get("entity_group") or ent.get("entity") or "ENT"
            start = ent.get("start")
            end = ent.get("end")
            if isinstance(start, int) and isinstance(end, int):
                _add_span(spans, start, end, 0.88, f"ner:{eg}")
            else:
                idx = text.find(word)
                if idx >= 0:
                    _add_span(spans, idx, idx + len(word), 0.75, f"ner:{eg}")

    return _merge_spans(spans)
