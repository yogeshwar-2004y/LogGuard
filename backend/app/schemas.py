"""Pydantic models for API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


Industry = Literal[
    "default",
    "healthcare",
    "finance",
    "manufacturing",
    "energy",
    "government",
    "cloud",
]

LogFormat = Literal["cef", "syslog", "json", "plain"]


class AnalyzeRequest(BaseModel):
    log_text: str = Field(..., min_length=1, description="Raw SIEM / log line(s)")
    industry: Industry = "default"


class MitreTechnique(BaseModel):
    id: str = Field(..., description="MITRE technique ID, e.g. T1059")
    name: str
    url: str
    confidence: float = Field(ge=0.0, le=1.0)


class IOC(BaseModel):
    type: str = Field(..., description="ip, domain, url, hash, user, process, email, file, other")
    value: str
    context: str | None = None


class TokenHighlight(BaseModel):
    start: int
    end: int
    score: float = Field(ge=0.0, le=1.0, description="Relative importance / suspicion")
    label: str | None = None


class PlaybookItem(BaseModel):
    title: str
    action: str
    sample_query: str | None = None


class PlaybookResponse(BaseModel):
    sector: str
    items: list[PlaybookItem]
    notes: str | None = None


class DetectionRules(BaseModel):
    """Sigma (YAML) + optional YARA generated from analysis context."""

    title: str
    sigma_yaml: str
    yara_rule: str | None = None
    false_positives: str
    severity_sigma_level: str


class AttackChainNode(BaseModel):
    id: str
    node_type: Literal["tactic", "technique", "ioc", "sector_risk"]
    label: str
    mitre_id: str | None = None
    mitre_url: str | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    ioc_type: str | None = None
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class AttackChainEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None
    strength: float | None = Field(None, ge=0.0, le=1.0)


class AttackChainGraph(BaseModel):
    nodes: list[AttackChainNode]
    edges: list[AttackChainEdge]


class AnalyzeResponse(BaseModel):
    format_detected: LogFormat
    severity: Literal["info", "low", "medium", "high", "critical"]
    severity_score: float = Field(ge=0.0, le=1.0)
    executive_summary: str
    risk_explanation: str
    mitre_techniques: list[MitreTechnique]
    iocs: list[IOC]
    token_highlights: list[TokenHighlight]
    playbook: PlaybookResponse
    detection_rules: DetectionRules
    attack_chain: AttackChainGraph
    model_notes: str | None = Field(None, description="HF fallback / model routing notes")
    processing_time_ms: int


class BatchLogItem(BaseModel):
    raw_log: str
    line_index: int | None = None


class BatchAnalyzeRequest(BaseModel):
    logs: list[BatchLogItem]
    industry: Industry = "default"


class CorrelationCluster(BaseModel):
    cluster_id: int
    log_indices: list[int]
    theme: str
    representative_snippet: str


class BatchAnalyzeResponse(BaseModel):
    results: list[AnalyzeResponse]
    clusters: list[CorrelationCluster]
    processing_time_ms: int


class DemoLogEntry(BaseModel):
    id: str
    title: str
    category: str
    raw_log: str
    expected_severity: str
    mitre_hint: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatFollowupRequest(BaseModel):
    messages: list[ChatMessage]
    industry: Industry = "default"
    context_log_snippet: str | None = Field(None, max_length=8000)


class HealthResponse(BaseModel):
    status: str
    hf_configured: bool


class TestSigmaRequest(BaseModel):
    sigma_yaml: str
    logs: list[str] = Field(..., max_length=300, description="Log lines to test (max 300)")


class TestSigmaResponse(BaseModel):
    match_count: int
    matching_indices: list[int]
    tokens_used: list[str]
    parse_error: str | None = None
