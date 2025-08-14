from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def load_training_data(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        # Generate synthetic dataset: features (abs_qty, abs_price_dev), label break{0,1}
        rng = np.random.default_rng(42)
        n = 500
        qty = rng.normal(5, 2, n)
        price_dev = rng.normal(0, 1, n)
        label = (np.abs(price_dev) + 0.1 * qty > 1.8).astype(int)
        df = pd.DataFrame({"abs_qty": np.abs(qty), "abs_price_dev": np.abs(price_dev), "break": label})
        return df
    return pd.read_csv(csv_path)


def train_model(df: pd.DataFrame) -> Pipeline:
    X = df[["abs_qty", "abs_price_dev"]].values
    y = df["break"].values
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, solver="lbfgs")),
        ]
    )
    pipe.fit(X, y)
    return pipe


def predict_breaks(model: Pipeline, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not candidates:
        return []
    X = np.array([[abs(c.get("quantity", 0)), abs(c.get("price_dev", 0))] for c in candidates])
    probs = model.predict_proba(X)[:, 1]
    out: List[Dict[str, Any]] = []
    for c, p in zip(candidates, probs):
        likely_cause = "Price deviation" if abs(c.get("price_dev", 0)) > 0.5 else "Quantity mismatch"
        action = "Review tolerance" if likely_cause == "Price deviation" else "Check allocation/account"
        out.append({**c, "probability": float(p), "likely_cause": likely_cause, "suggested_action": action})
    return out


