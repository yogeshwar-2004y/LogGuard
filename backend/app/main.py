"""
LogGuard AI — FastAPI application.

Privacy: request bodies are not persisted; logs exist only in memory for the duration of the request.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from typing import Annotated, get_args

from app.config import get_settings
from app.demo_logs import get_demo_logs
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    BatchLogItem,
    ChatFollowupRequest,
    HealthResponse,
    Industry,
    TestSigmaRequest,
    TestSigmaResponse,
)
from app.services.analyzer import analyze_log_text
from app.services.correlation import cluster_logs
from app.services.hf_inference import text_generate
from app.services.pdf_report import build_pdf_bytes
from app.services.sigma_tester import test_sigma_against_logs

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LogGuard AI",
    description="SIEM log threat classifier & SOC co-pilot (Hugging Face Inference + local correlation).",
    version="1.0.0",
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    s = get_settings()
    return HealthResponse(status="ok", hf_configured=bool(s.hf_token))


@app.get("/demo-logs")
async def demo_logs():
    return [d.model_dump() for d in get_demo_logs()]


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    s = get_settings()
    text = body.log_text.strip()
    if not text:
        raise HTTPException(400, "log_text is empty")
    if len(text) > s.max_log_chars:
        raise HTTPException(413, f"log_text exceeds {s.max_log_chars} characters")
    return await analyze_log_text(s, text, body.industry)


@app.post("/analyze-batch", response_model=BatchAnalyzeResponse)
async def analyze_batch_json(body: BatchAnalyzeRequest):
    s = get_settings()
    if len(body.logs) > s.max_batch_items:
        raise HTTPException(413, f"Max {s.max_batch_items} logs per batch")
    t0 = time.perf_counter()
    to_run: list[str] = []
    for item in body.logs:
        raw = item.raw_log.strip()
        if not raw:
            continue
        if len(raw) > s.max_log_chars:
            raise HTTPException(413, "One log exceeds max length")
        to_run.append(raw)

    if not to_run:
        return BatchAnalyzeResponse(results=[], clusters=[], processing_time_ms=0)

    sem = asyncio.Semaphore(2)

    async def one(log_text: str) -> AnalyzeResponse:
        async with sem:
            return await analyze_log_text(s, log_text, body.industry)

    results = await asyncio.gather(*[one(t) for t in to_run])
    clusters = cluster_logs(to_run) if len(to_run) >= 2 else []
    elapsed = int((time.perf_counter() - t0) * 1000)
    return BatchAnalyzeResponse(results=list(results), clusters=clusters, processing_time_ms=elapsed)


@app.post("/analyze-batch-upload", response_model=BatchAnalyzeResponse)
async def analyze_batch_upload(
    files: Annotated[list[UploadFile], File(description="One or more log files")],
    industry: Annotated[str, Form()] = "default",
):
    """Upload one or more .log / .txt / .csv / .json files; each line (or JSON array element) becomes a log event."""
    s = get_settings()
    if not files:
        raise HTTPException(400, "No files uploaded")
    raw_lines: list[str] = []
    for uf in files[:20]:
        data = await uf.read()
        if len(data) > s.max_log_chars * 2:
            raise HTTPException(413, "File too large")
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = str(data)
        name = (uf.filename or "").lower()
        if name.endswith(".json"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    for el in parsed:
                        raw_lines.append(json.dumps(el) if isinstance(el, (dict, list)) else str(el))
                elif isinstance(parsed, dict):
                    raw_lines.append(json.dumps(parsed))
                else:
                    raw_lines.append(str(parsed))
            except json.JSONDecodeError:
                raw_lines.extend(line for line in text.splitlines() if line.strip())
        else:
            raw_lines.extend(line for line in text.splitlines() if line.strip())
    if len(raw_lines) > s.max_batch_items:
        raw_lines = raw_lines[: s.max_batch_items]
    if not raw_lines:
        raise HTTPException(400, "No log lines found in upload")
    allowed = get_args(Industry)
    ind: Industry = industry if industry in allowed else "default"  # type: ignore[assignment]
    body = BatchAnalyzeRequest(
        logs=[BatchLogItem(raw_log=line, line_index=i) for i, line in enumerate(raw_lines)],
        industry=ind,
    )
    return await analyze_batch_json(body)


@app.post("/test-sigma", response_model=TestSigmaResponse)
async def test_sigma(body: TestSigmaRequest):
    """
    Heuristic match: extracts string tokens from Sigma YAML `detection` and scores uploaded log lines.
    Not a full Sigma engine; useful for quick validation in the UI.
    """
    if not body.logs:
        raise HTTPException(400, "logs array is empty")
    mc, idx, tokens, perr = test_sigma_against_logs(body.sigma_yaml, body.logs)
    return TestSigmaResponse(
        match_count=mc,
        matching_indices=idx,
        tokens_used=tokens,
        parse_error=perr,
    )


@app.post("/report/pdf")
async def export_pdf(result: AnalyzeResponse):
    pdf = build_pdf_bytes(result)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="logguard-report.pdf"'},
    )


@app.post("/chat-followup")
async def chat_followup(body: ChatFollowupRequest):
    s = get_settings()
    ctx = (body.context_log_snippet or "")[:6000]
    transcript = "\n".join(f"{m.role.upper()}: {m.content}" for m in body.messages[-8:])
    prompt = (
        "You are LogGuard AI SOC co-pilot. Answer concisely with bullets when helpful.\n"
        f"Industry: {body.industry}.\n"
        f"Optional log context:\n{ctx}\n\n"
        f"Conversation:\n{transcript}\n"
        "Assistant:"
    )
    reply, err = await text_generate(s, prompt, max_new_tokens=512)
    if err or not reply:
        raise HTTPException(503, f"Generation unavailable: {err or 'empty'}")
    return {"reply": reply}


@app.post("/chat-followup/stream")
async def chat_followup_stream(body: ChatFollowupRequest):
    s = get_settings()

    async def event_stream():
        ctx = (body.context_log_snippet or "")[:6000]
        transcript = "\n".join(f"{m.role.upper()}: {m.content}" for m in body.messages[-8:])
        prompt = (
            "You are LogGuard AI SOC co-pilot. Answer concisely.\n"
            f"Industry: {body.industry}.\n"
            f"Optional log context:\n{ctx}\n\n"
            f"Conversation:\n{transcript}\n"
            "Assistant:"
        )
        reply, err = await text_generate(s, prompt, max_new_tokens=512)
        if err or not reply:
            yield f"data: [error] {err or 'empty'}\n\n"
            return
        chunk_size = 48
        for i in range(0, len(reply), chunk_size):
            piece = reply[i : i + chunk_size]
            yield f"data: {json.dumps(piece)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
