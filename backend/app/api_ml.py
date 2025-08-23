from __future__ import annotations

import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .ml.predict import load_training_data, train_model, predict_breaks
from .security.auth import require_roles, User
from .db import get_session_optional
from .models import MLModel, PredictionBreak


router = APIRouter(prefix="/ml", tags=["ml"]) 


def _models_dir() -> Path:
    base = Path(os.getenv("TMP_DIR", "./tmp/opspilot")) / "models"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _save_model(obj: Any, model_id: str) -> Path:
    path = _models_dir() / f"{model_id}.pkl"
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return path


def _load_model(model_id: str) -> Any:
    path = _models_dir() / f"{model_id}.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)


@router.post("/train/predict-breaks")
def train_predict_breaks(user: User = Depends(require_roles("admin")), db: Session | None = Depends(get_session_optional)):
    df = load_training_data(Path("./tmp/training_data.csv"))
    model = train_model(df)
    ts = datetime.now(timezone.utc)
    model_id = f"predict_breaks_v1_{int(ts.timestamp())}"
    _save_model(model, model_id)
    if db is not None:
        meta = MLModel(
            model_id=model_id,
            kind="predict_breaks",
            version=1,
            trained_from=ts,
            run_window=None,
            metrics={"n": int(df.shape[0])},
            features={"names": ["abs_qty", "abs_price_dev"]},
            notes=None,
        )
        db.add(meta)
        db.commit()
    return {"model_id": model_id}


@router.post("/score/predict-breaks")
def score_predict_breaks(
    runId: str = Query(..., alias="runId"),
    user: User = Depends(require_roles("analyst", "admin")),
    db: Session | None = Depends(get_session_optional),
):
    # Find latest model id if present; otherwise, train ephemeral model
    model_id: str
    model_obj: Any
    if db is not None:
        row = db.query(MLModel).order_by(MLModel.trained_from.desc()).first()
        if row is not None:
            model_id = row.model_id
            model_obj = _load_model(model_id)
        else:
            df = load_training_data(Path("./tmp/training_data.csv"))
            model_obj = train_model(df)
            ts = datetime.now(timezone.utc)
            model_id = f"predict_breaks_ephemeral_{int(ts.timestamp())}"
    else:
        df = load_training_data(Path("./tmp/training_data.csv"))
        model_obj = train_model(df)
        model_id = "predict_breaks_ephemeral"

    # Candidates: synthesize a tiny set for demo; real impl would fetch features_records
    candidates = [
        {"record_id": f"R{i}", "quantity": i + 1, "price_dev": (0.2 * (i % 3))} for i in range(1, 11)
    ]
    feature_names = ["abs_qty", "abs_price_dev"]
    preds = predict_breaks(model_obj, candidates)

    # Compute simple contribution-based explanations (logistic regression coefs * scaled features)
    try:
        scaler = getattr(model_obj, "named_steps", {}).get("scaler")
        clf = getattr(model_obj, "named_steps", {}).get("clf")
        X = np.array([[abs(c.get("quantity", 0)), abs(c.get("price_dev", 0))] for c in candidates])
        Xs = scaler.transform(X) if scaler is not None else X
        coefs = getattr(clf, "coef_")[0] if clf is not None else np.zeros(Xs.shape[1])
        contribs = np.abs(Xs * coefs)
        top_labels: List[List[str]] = []
        for row in contribs:
            order = np.argsort(-row)
            labels = [feature_names[i] for i in order[:3]]
            top_labels.append(labels)
    except Exception:
        top_labels = [["abs_qty", "abs_price_dev"] for _ in preds]

    # Persist predictions if DB available
    if db is not None:
        ts = datetime.now(timezone.utc)
        for idx, p in enumerate(preds):
            pb = PredictionBreak(
                run_id=runId,
                record_id=str(p.get("record_id")),
                model_id=model_id,
                model_type="ml",
                p_break=int(round(float(p.get("probability", 0.0)) * 10000)),
                p_type=None,
                ttfr_bucket=None,
                autoclear_suggest=None,
                explanation_top={"likely_cause": p.get("likely_cause"), "suggested_action": p.get("suggested_action"), "top": top_labels[idx]},
                created_at=ts,
            )
            db.merge(pb)
        db.commit()

    high = sum(1 for p in preds if p.get("probability", 0) >= 0.7)
    med = sum(1 for p in preds if 0.4 <= p.get("probability", 0) < 0.7)
    low = sum(1 for p in preds if p.get("probability", 0) < 0.4)
    return {"runId": runId, "counts": {"high": high, "med": med, "low": low}, "total": len(preds)}


@router.get("/models/{model_id}")
def get_model(model_id: str, db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"model_id": model_id, "kind": "predict_breaks", "version": 1}
    m = db.get(MLModel, model_id)
    if not m:
        return {"model_id": model_id, "status": "missing"}
    return {
        "model_id": m.model_id,
        "kind": m.kind,
        "version": m.version,
        "trained_from": m.trained_from.isoformat(),
        "metrics": m.metrics,
        "features": m.features,
        "notes": m.notes,
    }


