"""Hugging Face Inference via huggingface_hub (Inference Providers routing)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from huggingface_hub import InferenceClient

from app.config import Settings

logger = logging.getLogger(__name__)

# Extra zero-shot models (NLI / zero-shot on HF Inference). MoritzLaurer IDs often 404 on router.
ZERO_SHOT_MODEL_FALLBACKS = (
    "typeform/distilbert-base-uncased-mnli",
    "facebook/bart-large-mnli",
)

# Chat completions return 400 for many models on router; text_generation (hf-inference) is tried first per model.
GENERATE_MODEL_FALLBACKS = (
    "Qwen/Qwen2.5-0.5B-Instruct",
    "microsoft/Phi-3-mini-4k-instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "google/flan-t5-base",
)

# Router rejects huge prompts with 400; keep well under context limits.
_MAX_GEN_PROMPT_CHARS = 10_000

CYBER_CANDIDATE_LABELS = [
    "benign routine IT maintenance or expected admin activity",
    "suspicious authentication or credential abuse",
    "malware ransomware or destructive impact",
    "network command and control or data exfiltration",
    "unauthorized cloud IAM or policy change",
    "industrial or OT protocol manipulation",
]


def _client(settings: Settings) -> InferenceClient:
    return InferenceClient(
        token=settings.hf_token or None,
        timeout=settings.hf_inference_timeout,
    )


async def zero_shot_classify(
    settings: Settings,
    text: str,
) -> tuple[dict[str, float] | None, str | None]:
    truncated = text[:8000]
    models: list[str] = []
    for m in (settings.hf_classify_model, *ZERO_SHOT_MODEL_FALLBACKS):
        if m and m not in models:
            models.append(m)

    def run() -> dict[str, float]:
        c = _client(settings)
        last: Exception | None = None
        for model_id in models:
            try:
                rows = c.zero_shot_classification(
                    truncated,
                    candidate_labels=CYBER_CANDIDATE_LABELS,
                    model=model_id,
                )
                return {r.label: float(r.score) for r in rows}
            except Exception as e:
                last = e
                logger.warning("zero_shot_classification model=%s failed: %s", model_id, e)
        raise last or RuntimeError("zero_shot: no model succeeded")

    try:
        return await asyncio.to_thread(run), None
    except Exception as e:
        logger.warning("zero_shot_classification failed: %s", e)
        return None, str(e)


async def ner_predict(
    settings: Settings,
    text: str,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    truncated = text[:4000]

    def run() -> list[dict[str, Any]]:
        c = _client(settings)
        rows = c.token_classification(truncated, model=settings.hf_ner_model)
        out = []
        for r in rows:
            d = r.model_dump() if hasattr(r, "model_dump") else dict(r)
            out.append(d)
        return out

    try:
        return await asyncio.to_thread(run), None
    except Exception as e:
        logger.warning("token_classification failed: %s", e)
        return None, str(e)


def _chat_reply(c: InferenceClient, model: str, prompt: str, max_new_tokens: int) -> str:
    out = c.chat_completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_new_tokens,
        temperature=0.2,
    )
    if not out.choices:
        return ""
    msg = out.choices[0].message
    content = getattr(msg, "content", None) if msg is not None else None
    return str(content or "").strip()


def _text_gen_reply(c: InferenceClient, model: str, prompt: str, max_new_tokens: int) -> str:
    # T5 is seq2seq; shorter completions are more reliable on small models.
    mtok = min(max_new_tokens, 384) if "flan-t5" in model.lower() else max_new_tokens
    out = c.text_generation(
        prompt,
        model=model,
        max_new_tokens=mtok,
        temperature=0.2,
        return_full_text=False,
    )
    if isinstance(out, str):
        return out.strip()
    gen = getattr(out, "generated_text", None)
    if gen:
        return str(gen).strip()
    return str(out).strip()


def _generate_one_model(settings: Settings, model: str, prompt: str, max_new_tokens: int) -> str:
    """Prefer text_generation (classic hf-inference) — router /v1/chat/completions often returns 400."""
    c = _client(settings)
    last_err: str | None = None
    for fn in (_text_gen_reply, _chat_reply):
        try:
            text = fn(c, model, prompt, max_new_tokens)
            if text:
                return text
        except Exception as e:
            last_err = str(e)
            logger.debug("generate %s via %s: %s", model, fn.__name__, e)
            continue
    raise RuntimeError(last_err or f"no method succeeded for {model}")


async def text_generate(
    settings: Settings,
    prompt: str,
    max_new_tokens: int = 512,
) -> tuple[str | None, str | None]:
    trimmed = prompt[:_MAX_GEN_PROMPT_CHARS] if len(prompt) > _MAX_GEN_PROMPT_CHARS else prompt
    if len(trimmed) < len(prompt):
        logger.info("text_generate: truncated prompt %s → %s chars", len(prompt), len(trimmed))

    models: list[str] = []
    for m in (settings.hf_generate_model, *GENERATE_MODEL_FALLBACKS):
        if m and m not in models:
            models.append(m)

    def run() -> str:
        last: Exception | None = None
        for model_id in models:
            try:
                return _generate_one_model(settings, model_id, trimmed, max_new_tokens)
            except Exception as e:
                last = e
                logger.warning("text_generate model=%s failed: %s", model_id, e)
        raise last or RuntimeError("generate: no model succeeded")

    try:
        text_out = await asyncio.to_thread(run)
        return text_out, None
    except Exception as e:
        logger.warning("text_generate failed: %s", e)
        return None, str(e)


def scores_to_severity(scores: dict[str, float] | None) -> tuple[str, float, str | None]:
    """Map zero-shot labels to severity + scalar score."""
    if not scores:
        return "medium", 0.5, None
    top_label = max(scores, key=lambda k: scores[k])
    top = scores[top_label]
    benign = scores.get(
        "benign routine IT maintenance or expected admin activity",
        0.0,
    )
    if benign >= 0.55 and benign >= top * 0.95:
        return "info", float(benign), top_label
    threat_score = max(
        scores.get("suspicious authentication or credential abuse", 0.0),
        scores.get("malware ransomware or destructive impact", 0.0),
        scores.get("network command and control or data exfiltration", 0.0),
        scores.get("unauthorized cloud IAM or policy change", 0.0),
        scores.get("industrial or OT protocol manipulation", 0.0),
    )
    s = float(max(threat_score, 1.0 - benign))
    if s >= 0.85:
        return "critical", s, top_label
    if s >= 0.65:
        return "high", s, top_label
    if s >= 0.45:
        return "medium", s, top_label
    if s >= 0.25:
        return "low", s, top_label
    return "info", s, top_label


def keyword_fallback_severity(text: str) -> tuple[str, float]:
    t = text.lower()
    score = 0.15
    if any(x in t for x in ("ransom", "encrypt", "exfil", "mimikatz", "lsass dump")):
        score += 0.45
    if any(x in t for x in ("putuserpolicy", "assumerole", "bulk_export", "modbus write")):
        score += 0.35
    if any(x in t for x in ("failed password", "brute", "beacon", "curl/", "mfa")):
        score += 0.25
    if "reboot_pending=false" in t and "wsus" in t:
        score = min(score, 0.2)
    sev = "info"
    if score >= 0.85:
        sev = "critical"
    elif score >= 0.65:
        sev = "high"
    elif score >= 0.45:
        sev = "medium"
    elif score >= 0.3:
        sev = "low"
    return sev, min(1.0, score)
