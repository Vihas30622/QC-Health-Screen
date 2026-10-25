"""
ml/common/evaluation.py
=========================
Computes every metric Section 11 of the spec requires be reported for
every model on every disease: accuracy, precision, recall, F1, ROC-AUC,
confusion matrix, training time, inference time. Nothing here is
fabricated — every number is computed from actual predictions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class EvalResult:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: Optional[float]
    confusion_matrix: list
    training_time_sec: float
    inference_time_sec: float
    n_features: int
    extra: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4) if self.roc_auc is not None else None,
            "confusion_matrix": self.confusion_matrix,
            "training_time_sec": round(self.training_time_sec, 4),
            "inference_time_sec": round(self.inference_time_sec, 6),
            "n_features": self.n_features,
            **self.extra,
        }


def fit_and_evaluate(
    model,
    model_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    extra: Optional[Dict[str, Any]] = None,
) -> EvalResult:
    t0 = time.perf_counter()
    model.fit(X_train, y_train)
    training_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    y_pred = model.predict(X_test)
    inference_time = (time.perf_counter() - t0) / max(len(X_test), 1)

    roc_auc = None
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X_test)[:, 1]
            roc_auc = float(roc_auc_score(y_test, y_proba))
        except (ValueError, IndexError, AttributeError, RuntimeError):
            roc_auc = None

    result = EvalResult(
        model_name=model_name,
        accuracy=float(accuracy_score(y_test, y_pred)),
        precision=float(precision_score(y_test, y_pred, zero_division=0)),
        recall=float(recall_score(y_test, y_pred, zero_division=0)),
        f1=float(f1_score(y_test, y_pred, zero_division=0)),
        roc_auc=roc_auc,
        confusion_matrix=confusion_matrix(y_test, y_pred).tolist(),
        training_time_sec=training_time,
        inference_time_sec=inference_time,
        n_features=X_train.shape[1],
        extra=extra or {},
    )
    return result
