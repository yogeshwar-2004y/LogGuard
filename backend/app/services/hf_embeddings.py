"""Single shared MiniLM loader + HF Inference embeddings (avoids duplicate PyTorch models in RAM)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sklearn.preprocessing import Normalizer


@lru_cache(maxsize=1)
def get_sentence_transformer():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_local_minilm(texts: list[str], *, batch_size: int = 32) -> np.ndarray:
    """Encode with one cached SentenceTransformer (normalize_embeddings=True)."""
    n = len(texts)
    bs = min(batch_size, max(1, n))
    model = get_sentence_transformer()
    return np.asarray(
        model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=bs,
        ),
        dtype=np.float32,
    )


def embed_hf_remote(texts: list[str], model: str, token: str | None) -> np.ndarray:
    """One embedding per log via Hugging Face Inference (feature_extraction)."""
    from huggingface_hub import InferenceClient

    client = InferenceClient(token=token)
    rows: list[np.ndarray] = []
    for t in texts:
        chunk = t[:8000]
        arr = np.asarray(
            client.feature_extraction(chunk, model=model, truncate=True),
            dtype=np.float32,
        )
        if arr.ndim == 2 and arr.size:
            vec = arr.mean(axis=0)
        else:
            vec = arr.reshape(-1)
        rows.append(vec)
    X = np.vstack(rows)
    return Normalizer().fit_transform(X)
