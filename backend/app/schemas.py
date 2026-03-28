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
    # Batch / Isolation Forest (optional; set on batch responses only)
    anomaly_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Relative anomaly score within batch (Isolation Forest on MiniLM embeddings)",
    )
    isolation_anomaly_flag: bool = Field(
        False,
        description="True when anomaly_score exceeds secondary detector threshold",
    )


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


class TfIdfKeywordEntry(BaseModel):
    term: str
    score: float = Field(..., description="Aggregated TF-IDF weight for this incident")


class SimilarityIncident(BaseModel):
    """Logs linked by pairwise cosine similarity > threshold (TF-IDF space)."""

    incident_id: int
    log_indices: list[int]
    mean_cosine_similarity: float = Field(..., ge=0.0, le=1.0)
    min_cosine_similarity: float = Field(..., ge=0.0, le=1.0)


class TfidfKeywordsByIncident(BaseModel):
    incident_id: int
    keywords: list[TfIdfKeywordEntry]


class BatchAnalyzeResponse(BaseModel):
    results: list[AnalyzeResponse]
    clusters: list[CorrelationCluster]
    processing_time_ms: int
    incidents: list[SimilarityIncident] = Field(default_factory=list)
    tfidf_keywords: list[TfidfKeywordsByIncident] = Field(default_factory=list)
    anomaly_scores: list[float] = Field(
        default_factory=list,
        description="Per-log scores aligned with results[] (0–1, higher = more anomalous in batch)",
    )


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
