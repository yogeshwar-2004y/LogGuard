"""Batch log correlation: sentence-transformers when installed, else TF–IDF + clustering."""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer

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


def cluster_logs(log_texts: list[str]) -> list[CorrelationCluster]:
    if len(log_texts) < 2:
        return []
    try:
        try:
            X = _embed_st(log_texts)
        except Exception:
            X = _tokenize_logs(log_texts)
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
