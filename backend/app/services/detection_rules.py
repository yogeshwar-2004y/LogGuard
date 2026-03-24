"""Sigma + YARA rule generation (LLM + deterministic templates)."""

from __future__ import annotations

import re
from textwrap import dedent

import yaml

from app.config import Settings
from app.schemas import DetectionRules, IOC, Industry, MitreTechnique
from app.services.hf_inference import text_generate

_SEVERITY_TO_SIGMA_LEVEL = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "informational",
}


def _mitre_tags(techniques: list[MitreTechnique]) -> list[str]:
    tags: list[str] = []
    for t in techniques[:12]:
        tid = t.id.upper().replace(".", ".")
        if re.match(r"^T\d{4}", tid):
            tags.append(f"attack.{tid.lower()}")
    return tags or ["attack.execution"]


def _title_from_context(industry: Industry, techniques: list[MitreTechnique], severity: str) -> str:
    parts = [f"LogGuard — {industry}", severity.upper()]
    if techniques:
        parts.append(techniques[0].id)
    return " / ".join(parts)


def _template_sigma(
    title: str,
    log_sample: str,
    techniques: list[MitreTechnique],
    iocs: list[IOC],
    industry: Industry,
    sigma_level: str,
) -> str:
    tags = _mitre_tags(techniques)
    tag_lines = "\n".join(f"    - {tg}" for tg in tags)
    contains: list[str] = []
    for ioc in iocs[:8]:
        v = ioc.value.replace("'", "''")[:120]
        if len(v) >= 3:
            contains.append(f"      - '{v}'")
    if not contains:
        line = log_sample[:200].replace("'", "''")
        contains.append(f"      - '{line}'")
    contains_yaml = "\n".join(contains[:12])
    safe_title = title.replace('"', "'")[:200]
    rule_id = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")[:60] or "logguard-generated"
    return dedent(
        f"""
        title: "{safe_title}"
        id: {rule_id}
        status: experimental
        description: |
          Auto-generated from LogGuard AI analysis ({industry} sector).
          Review and tune before production.
        author: LogGuard AI
        references:
          - https://attack.mitre.org/
        logsource:
          category: process_creation
          product: windows
        detection:
          selection_keywords:
            CommandLine|contains:
{contains_yaml}
          condition: selection_keywords
        falsepositives:
          - Legitimate administrative scripts and approved change windows
          - Security scanning and vulnerability assessment tools
        level: {sigma_level}
        tags:
{tag_lines}
        """
    ).strip()


def _template_yara(title: str, iocs: list[IOC], log_sample: str) -> str:
    strings_block: list[str] = []
    for idx, ioc in enumerate(iocs[:12]):
        esc = ioc.value.replace("\\", "\\\\").replace('"', '\\"')[:200]
        if len(esc) >= 2:
            strings_block.append(f'        $s{idx} = "{esc}" ascii wide')
    if not strings_block:
        esc = log_sample[:160].replace("\\", "\\\\").replace('"', '\\"')
        strings_block.append(f'        $s0 = "{esc}" ascii wide')
    str_body = "\n".join(strings_block)
    cond = " or ".join(f"$s{i}" for i in range(len(strings_block)))
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", title)[:40] or "LogGuardGenerated"
    return dedent(
        f"""
        rule {safe_name} {{
            meta:
                description = "LogGuard AI generated — review before deploy"
                author = "LogGuard AI"
            strings:
{str_body}
            condition:
                any of them
        }}
        """
    ).strip()


def _parse_llm_rules(text: str) -> tuple[str | None, str | None]:
    sigma = None
    yara = None
    m_sigma = re.search(r"```ya?ml\s*([\s\S]*?)```", text, re.I)
    if m_sigma:
        sigma = m_sigma.group(1).strip()
    m_yar = re.search(r"```ya?r?\s*([\s\S]*?)```", text, re.I)
    if m_yar:
        yara = m_yar.group(1).strip()
    return sigma, yara


def _validate_sigma_yaml(s: str) -> bool:
    try:
        d = yaml.safe_load(s)
        return isinstance(d, dict) and "detection" in d
    except Exception:
        return False


async def build_detection_rules(
    settings: Settings,
    log_text: str,
    industry: Industry,
    severity: str,
    techniques: list[MitreTechnique],
    iocs: list[IOC],
) -> DetectionRules:
    sigma_level = _SEVERITY_TO_SIGMA_LEVEL.get(severity, "medium")
    title = _title_from_context(industry, techniques, severity)
    mitre_summary = ", ".join(f"{t.id} ({t.name})" for t in techniques[:8]) or "none"
    ioc_summary = ", ".join(f"{i.type}:{i.value[:40]}" for i in iocs[:15]) or "none"
    sample = log_text[:4000]

    prompt = dedent(
        f"""
        You are an expert detection engineer. Output ONLY two fenced code blocks: first Sigma (YAML), then YARA.

        Requirements for Sigma:
        - Valid Sigma YAML: title, id, status, description, author: LogGuard AI, logsource, detection, falsepositives, level ({sigma_level}), tags with attack.mitre technique tags from: {mitre_summary}
        - Use realistic Windows process_creation or appropriate logsource for this log sample
        - detection must reference observable strings from the log / IOCs

        Requirements for YARA:
        - Valid YARA with meta (author LogGuard AI), strings, condition any of them
        - Include string patterns for notable IOC substrings

        Context:
        industry={industry}
        severity={severity}
        MITRE: {mitre_summary}
        IOCs: {ioc_summary}

        LOG SAMPLE:
        {sample}

        Output format:
        ```yaml
        ... sigma ...
        ```
        ```yar
        ... yara ...
        ```
        """
    ).strip()

    sigma_yaml = _template_sigma(title, log_text, techniques, iocs, industry, sigma_level)
    yara_rule = _template_yara(title, iocs, log_text)

    gen, err = await text_generate(settings, prompt, max_new_tokens=1800)
    if gen and not err:
        s2, y2 = _parse_llm_rules(gen)
        if s2 and _validate_sigma_yaml(s2):
            sigma_yaml = s2
        if y2 and "rule " in y2.lower():
            yara_rule = y2

    if not _validate_sigma_yaml(sigma_yaml):
        sigma_yaml = _template_sigma(title, log_text, techniques, iocs, industry, sigma_level)

    return DetectionRules(
        title=title,
        sigma_yaml=sigma_yaml,
        yara_rule=yara_rule,
        false_positives="Legitimate administrative activity, change windows, and security tooling.",
        severity_sigma_level=sigma_level,
    )
