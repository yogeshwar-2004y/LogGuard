"""
Batch-only NLP insights: TF-IDF + cosine similarity incident grouping, and
Isolation Forest anomaly scores on sentence-transformers embeddings.

Runs alongside HF/transformer classification; does not replace it.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, Normalizer

from app.schemas import SimilarityIncident, TfIdfKeywordEntry, TfidfKeywordsByIncident

logger = logging.getLogger(__name__)

# Cosine similarity above this links two logs in the same TF-IDF "incident" (single-link components).
SIMILARITY_THRESHOLD = 0.75
TOP_KEYWORDS = 10


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())[:8000]


@lru_cache(maxsize=1)
def _sentence_model():
    """Lazy-load MiniLM once per worker (CPU-friendly small model)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _mean_pairwise_cosine(sim_matrix: np.ndarray, indices: list[int]) -> tuple[float, float]:
    """Return (mean, min) pairwise cosine for distinct pairs inside the index set."""
    if len(indices) < 2:
        return 1.0, 1.0
    idx = np.array(indices, dtype=int)
    sub = sim_matrix[np.ix_(idx, idx)]
    pairs = []
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            pairs.append(float(sub[i, j]))
    return float(np.mean(pairs)), float(np.min(pairs))


def compute_tfidf_incidents(logs: list[str]) -> tuple[list[SimilarityIncident], list[TfidfKeywordsByIncident]]:
    """
    Vectorize logs with TF-IDF, cosine similarity graph (edge if sim > threshold),
    extract connected components with >= 2 logs as incidents; top TF-IDF terms per incident.
    """
    if len(logs) < 2:
        return [], []

    cleaned = [_clean(t) for t in logs]
    try:
        vectorizer = TfidfVectorizer(
            max_features=4096,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w\w+\b|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
        )
        X = vectorizer.fit_transform(cleaned)
        X = Normalizer().fit_transform(X)
        S = cosine_similarity(X)
    except Exception as e:
        logger.warning("TF-IDF incident grouping failed: %s", e)
        return [], []

    n = len(logs)
    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if S[i, j] > SIMILARITY_THRESHOLD:
                uf.union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        r = uf.find(i)
        groups.setdefault(r, []).append(i)

    feature_names = np.array(vectorizer.get_feature_names_out())
    incidents: list[SimilarityIncident] = []
    kw_groups: list[TfidfKeywordsByIncident] = []
    incident_id = 0

    for _root, indices in sorted(groups.items(), key=lambda x: -len(x[1])):
        if len(indices) < 2:
            continue
        indices.sort()
        mean_sim, min_sim = _mean_pairwise_cosine(S, indices)
        row_sum = np.asarray(X[indices].sum(axis=0)).ravel()
        if row_sum.size == 0:
            continue
        top_idx = np.argsort(row_sum)[::-1][:TOP_KEYWORDS]
        keywords = [
            TfIdfKeywordEntry(term=str(feature_names[j]), score=float(row_sum[j]))
            for j in top_idx
            if row_sum[j] > 0
        ][:TOP_KEYWORDS]

        incidents.append(
            SimilarityIncident(
                incident_id=incident_id,
                log_indices=indices,
                mean_cosine_similarity=round(mean_sim, 4),
                min_cosine_similarity=round(min_sim, 4),
            )
        )
        kw_groups.append(
            TfidfKeywordsByIncident(incident_id=incident_id, keywords=keywords),
        )
        incident_id += 1

    return incidents, kw_groups


def compute_isolation_anomaly_scores(logs: list[str]) -> list[float]:
    """
    Encode logs with MiniLM; IsolationForest score_samples (higher = more inlier).
    Map to [0, 1] where higher = more anomalous (relative to this batch).
    """
    n = len(logs)
    if n < 2:
        return [0.0] * n

    try:
        model = _sentence_model()
        emb = model.encode(
            [_clean(t) for t in logs],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=min(32, n),
        )
        emb = np.asarray(emb, dtype=np.float32)
        clf = IsolationForest(
            n_estimators=min(200, max(50, n * 4)),
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(emb)
        # score_samples: higher = more normal / inlier
        raw = clf.score_samples(emb).reshape(-1, 1)
        inv = -raw
        scaled = MinMaxScaler().fit_transform(inv).ravel()
        return [float(round(float(x), 4)) for x in scaled]
    except Exception as e:
        logger.warning("Isolation Forest anomaly scoring failed: %s", e)
        return [0.0] * n


def compute_batch_nlp_insights(
    logs: list[str],
) -> tuple[list[SimilarityIncident], list[TfidfKeywordsByIncident], list[float]]:
    """TF-IDF incidents + keyword tables + per-log anomaly scores (batch-aligned)."""
    incidents, tfidf_keywords = compute_tfidf_incidents(logs)
    anomaly_scores = compute_isolation_anomaly_scores(logs)
    if len(anomaly_scores) != len(logs):
        anomaly_scores = [0.0] * len(logs)
    return incidents, tfidf_keywords, anomaly_scores
