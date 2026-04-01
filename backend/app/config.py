"""Application settings (env-driven for Hugging Face and deployment).

Render injects ``PORT`` for the HTTP server (see Dockerfile / start command).
Set ``CORS_ORIGINS`` (or ``cors_origins``) to your Vercel production URL and any
preview URLs you use, comma-separated.
"""

from functools import lru_cache

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
    # When true (recommended on Render without sentence-transformers), batch clustering uses HF feature_extraction.
    hf_use_remote_embeddings: bool = False

    max_log_chars: int = 50_000
    max_batch_items: int = 200
    # Browser origins allowed by CORS (e.g. https://your-app.vercel.app,http://localhost:5173).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://log-guard-seven.vercel.app/"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
