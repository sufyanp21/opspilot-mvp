from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from typing import Optional

try:
    import hdbscan  # type: ignore
except Exception:  # pragma: no cover
    hdbscan = None  # type: ignore


def vectorize_exception(ex: Dict[str, Any]) -> np.ndarray:
    # Simple vectorization using presence of mismatch categories and magnitudes
    details = ex.get("details", {}) or {}
    has_price = 1.0 if "price" in details else 0.0
    has_qty = 1.0 if "quantity" in details else 0.0
    price_mag = 0.0
    qty_mag = 0.0
    if "price" in details:
        d = details["price"]
        price_mag = abs(float(d.get("external", d.get("auth", 0)) or 0) - float(d.get("internal", 0) or 0))
    if "quantity" in details:
        d = details["quantity"]
        qty_mag = abs(float(d.get("external", d.get("auth", 0)) or 0) - float(d.get("internal", 0) or 0))
    return np.array([has_price, has_qty, price_mag, qty_mag], dtype=float)


def cosine_similarity_matrix(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-8
    Xn = X / norms
    return np.clip(Xn @ Xn.T, -1.0, 1.0)


def naive_cluster(exceptions: List[Dict[str, Any]], threshold: float = 0.8) -> List[Dict[str, Any]]:
    if not exceptions:
        return []
    X = np.vstack([vectorize_exception(ex) for ex in exceptions])
    S = cosine_similarity_matrix(X)
    n = S.shape[0]
    visited = set()
    clusters: List[List[int]] = []
    for i in range(n):
        if i in visited:
            continue
        cluster = [i]
        visited.add(i)
        for j in range(i + 1, n):
            if j not in visited and S[i, j] >= threshold:
                cluster.append(j)
                visited.add(j)
        clusters.append(cluster)
    out: List[Dict[str, Any]] = []
    for idx, ids in enumerate(clusters):
        out.append({"cluster_id": idx, "members": [exceptions[k] for k in ids], "size": len(ids)})
    return out


def hdbscan_cluster(exceptions: List[Dict[str, Any]], min_cluster_size: int = 2) -> List[Dict[str, Any]]:
    if hdbscan is None or not exceptions:
        return naive_cluster(exceptions)
    X = np.vstack([vectorize_exception(ex) for ex in exceptions])
    # Cosine-like space normalization improves distance behavior
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-8
    Xn = X / norms
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    labels = clusterer.fit_predict(Xn)
    clusters: Dict[int, List[int]] = {}
    for idx, label in enumerate(labels):
        if label == -1:  # noise → its own singleton cluster
            clusters.setdefault(idx + 100000, []).append(idx)
        else:
            clusters.setdefault(int(label), []).append(idx)
    out: List[Dict[str, Any]] = []
    for cid, members in clusters.items():
        out.append({"cluster_id": cid, "members": [exceptions[m] for m in members], "size": len(members)})
    return out


def cluster_exceptions(exceptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Prefer HDBSCAN if available
    return hdbscan_cluster(exceptions)


