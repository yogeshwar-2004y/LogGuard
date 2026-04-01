"""Application settings (env-driven for Hugging Face and deployment).

Render injects ``PORT`` for the HTTP server (see Dockerfile / start command).
Set ``CORS_ORIGINS`` (or ``cors_origins``) to your Vercel production URL and any
preview URLs you use, comma-separated. Use the scheme + host only (no path); a
trailing slash is stripped so it still matches the browser ``Origin`` header.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    hf_token: str | None = None

    # Zero-shot / NER / generation / remote embeddings (InferenceClient → Inference Providers).
    # DistilBERT-MNLI is smaller and tends to avoid 504s vs bart-large on shared inference.
    hf_classify_model: str = "typeform/distilbert-base-uncased-mnli"
    hf_ner_model: str = "dslim/bert-base-NER"
    hf_generate_model: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
    # Seconds for HF router calls (zero-shot / NER / generation); raise if Bart or large models time out often.
    hf_inference_timeout: float = 90.0
    hf_embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # When true and HF_TOKEN is set, batch clustering + anomaly use HF feature_extraction (saves RAM vs local PyTorch on Render).
    hf_use_remote_embeddings: bool = True

    max_log_chars: int = 50_000
    max_batch_items: int = 200
    # Browser origins allowed by CORS (scheme + host, no path). Override with CORS_ORIGINS on Render.
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://log-guard-seven.vercel.app"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _cors_origins_fallback(cls, v: object) -> object:
        # Render sometimes has CORS_ORIGINS set to an empty string — that would allow no explicit origins.
        if isinstance(v, str) and not v.strip():
            return (
                "http://localhost:5173,http://127.0.0.1:5173,"
                "https://log-guard-seven.vercel.app"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        # Browsers send Origin without a trailing slash; exact string match otherwise fails.
        # Strip quotes (env panels sometimes wrap values in "…").
        out: list[str] = []
        for o in self.cors_origins.split(","):
            s = o.strip().strip('"').strip("'").rstrip("/")
            if s:
                out.append(s)
        return out

    @property
    def cors_origin_regex(self) -> str | None:
        """Match any *.vercel.app HTTPS origin (prod + preview) when explicit list/env is wrong."""
        # Hyphen must be first/last in the class — [a-zA-Z0-9.-] is ambiguous for ranges.
        return r"^https://[a-zA-Z0-9][-a-zA-Z0-9.]*\.vercel\.app$"


@lru_cache
def get_settings() -> Settings:
    return Settings()
