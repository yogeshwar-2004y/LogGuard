"""Orchestrates format detection, HF calls, IOC/MITRE, and summaries."""

from __future__ import annotations

import time

from app.config import Settings, get_settings
from app.schemas import AnalyzeResponse, Industry
from app.services.format_detector import detect_format
from app.services.highlights import build_highlights
from app.services.hf_inference import (
    keyword_fallback_severity,
    ner_predict,
    scores_to_severity,
    text_generate,
    zero_shot_classify,
)
from app.services.attack_chain import build_attack_chain_graph
from app.services.detection_rules import build_detection_rules
from app.services.ioc_extract import extract_iocs_from_text, merge_ner_entities
from app.services.mitre_map import map_keywords_to_mitre
from app.services.playbook import build_playbook


def _template_summary(text: str, severity: str, fmt: str) -> tuple[str, str]:
    """Deterministic executive summary + risk explanation when HF generation fails."""
    head = text.strip().split("\n")[0][:400]
    summary = (
        f"Detected format: {fmt}. Automated assessment rated this event as **{severity.upper()}** severity. "
        f"The log excerpt shows: {head}{'…' if len(text) > 400 else ''}"
    )
    risk = (
        "Prioritize validation against your authoritative telemetry (EDR, proxy, IAM). "
        "Correlate user, host, and network indicators across the last 24–72 hours to rule out false positives."
    )
    if severity in ("high", "critical"):
        risk += " Treat as potential active threat; initiate containment per runbook if confirmed."
    return summary, risk


async def analyze_log_text(
    settings: Settings,
    log_text: str,
    industry: Industry,
    mitre_hints: list[str] | None = None,
) -> AnalyzeResponse:
    t0 = time.perf_counter()
    notes: list[str] = []
    fmt = detect_format(log_text)

    zscores, zerr = await zero_shot_classify(settings, log_text)
    if zerr:
        notes.append(f"classify:{zerr}")
    if zscores:
        severity, severity_score, top_lab = scores_to_severity(zscores)
        if top_lab:
            notes.append(f"classify_top:{top_lab[:80]}")
    else:
        severity, severity_score = keyword_fallback_severity(log_text)
        notes.append("classify:fallback_keywords")

    ner_list, nerr = await ner_predict(settings, log_text)
    if nerr:
        notes.append(f"ner:{nerr}")
    if ner_list:
        iocs = merge_ner_entities(log_text, ner_list)
    else:
        iocs = extract_iocs_from_text(log_text)

    mitre = map_keywords_to_mitre(log_text, mitre_hints)
    highlights = build_highlights(log_text, ner_list)

    prompt = (
        "You are LogGuard AI, an enterprise SOC assistant. Given the security log below, write:\n"
        "1) Executive summary (2 short sentences, non-technical).\n"
        "2) Risk explanation (2 sentences for analysts).\n"
        f"Industry context: {industry}. Severity hint: {severity}.\n\n"
        f"LOG:\n{log_text[:6000]}\n"
    )
    gen, gerr = await text_generate(settings, prompt, max_new_tokens=400)
    if gerr or not gen:
        notes.append(f"generate:{gerr or 'empty'}")
        executive_summary, risk_explanation = _template_summary(log_text, severity, fmt)
    else:
        parts = gen.split("\n")
        executive_summary = parts[0][:1200] if parts else gen[:1200]
        risk_explanation = "\n".join(parts[1:])[:2000] if len(parts) > 1 else gen[:2000]

    playbook = build_playbook(industry)
    iocs_limited = iocs[:80]
    attack_chain = build_attack_chain_graph(log_text, industry, severity, mitre, iocs_limited)
    detection_rules = await build_detection_rules(
        settings, log_text, industry, severity, mitre, iocs_limited
    )

    elapsed = int((time.perf_counter() - t0) * 1000)
    return AnalyzeResponse(
        format_detected=fmt,
        severity=severity,  # type: ignore[arg-type]
        severity_score=round(severity_score, 4),
        executive_summary=executive_summary.strip(),
        risk_explanation=risk_explanation.strip(),
        mitre_techniques=mitre,
        iocs=iocs_limited,
        token_highlights=highlights[:200],
        playbook=playbook,
        detection_rules=detection_rules,
        attack_chain=attack_chain,
        model_notes="; ".join(notes) if notes else None,
        processing_time_ms=elapsed,
    )


async def analyze_with_client(
    log_text: str,
    industry: Industry,
    mitre_hints: list[str] | None = None,
) -> AnalyzeResponse:
    settings = get_settings()
    return await analyze_log_text(settings, log_text, industry, mitre_hints)
