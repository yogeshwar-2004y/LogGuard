"""Application settings (env-driven for Hugging Face and deployment)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    hf_token: str | None = None

    # Zero-shot / NER / generation (override via env HF_*). Defaults pick models commonly routed on Inference Providers.
    hf_classify_model: str = "facebook/bart-large-mnli"
    hf_ner_model: str = "dslim/bert-base-NER"
    hf_generate_model: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct"

    max_log_chars: int = 50_000
    max_batch_items: int = 200
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
