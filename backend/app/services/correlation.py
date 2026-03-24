"""Batch log correlation: optional HF Inference embeddings, else sentence-transformers, else TF–IDF."""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer

from app.config import get_settings
from app.schemas import CorrelationCluster

logger = logging.getLogger(__name__)


def _tokenize_logs(texts: list[str]) -> np.ndarray:
    """Lightweight log-aware vectors (no PyTorch)."""
    cleaned = [re.sub(r"\s+", " ", t.lower())[:8000] for t in texts]
    vectorizer = TfidfVectorizer(
        max_features=384,
        ngram_range=(1, 2),
        min_df=1,
        token_pattern=r"(?u)\b\w\w+\b|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
    )
    X = vectorizer.fit_transform(cleaned)
    X = Normalizer().fit_transform(X)
    return X.toarray()


@lru_cache(maxsize=1)
def _st_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def _embed_st(texts: list[str]) -> np.ndarray:
    model = _st_model()
    return np.asarray(model.encode(texts, normalize_embeddings=True))


def _embed_hf_remote(texts: list[str], model: str, token: str | None) -> np.ndarray:
    """One embedding per log via Hugging Face Inference (feature_extraction API)."""
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


def cluster_logs(log_texts: list[str]) -> list[CorrelationCluster]:
    if len(log_texts) < 2:
        return []
    settings = get_settings()
    try:
        X: np.ndarray | None = None
        if settings.hf_use_remote_embeddings and settings.hf_token:
            try:
                X = _embed_hf_remote(
                    log_texts,
                    settings.hf_embeddings_model,
                    settings.hf_token,
                )
                logger.info("Batch clustering vectors: Hugging Face Inference (embeddings)")
            except Exception as e:
                logger.warning("HF remote embeddings failed, trying local / TF-IDF: %s", e)
                X = None
        if X is None:
            try:
                X = _embed_st(log_texts)
                logger.debug("Batch clustering vectors: sentence-transformers")
            except Exception:
                X = _tokenize_logs(log_texts)
                logger.debug("Batch clustering vectors: TF-IDF")
        n = len(log_texts)
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=0.55,
            metric="cosine",
            linkage="average",
        )
        labels = clustering.fit_predict(X)
    except Exception as e:
        logger.warning("Clustering failed: %s", e)
        return []

    clusters: dict[int, list[int]] = {}
    for idx, lab in enumerate(labels):
        clusters.setdefault(int(lab), []).append(idx)
    out: list[CorrelationCluster] = []
    for cid, indices in sorted(clusters.items(), key=lambda x: -len(x[1])):
        snippet = log_texts[indices[0]][:180].replace("\n", " ")
        theme = f"Cluster {cid} ({len(indices)} events)"
        out.append(
            CorrelationCluster(
                cluster_id=cid,
                log_indices=indices,
                theme=theme,
                representative_snippet=snippet + ("…" if len(log_texts[indices[0]]) > 180 else ""),
            )
        )
    return out
