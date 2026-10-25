"""
services/model_status.py
==========================
Reads whatever `ml/training/train_disease.py` actually saved to
`models/<disease>/metrics.json` and surfaces it to the API. This module
never computes or invents a metric itself — it only reports what
training already measured, on disk, in advance. If no metrics file
exists for a disease, that disease has no trained model and the API
says so rather than returning a placeholder number.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

MODELS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "models"
)


def _metrics_path(disease_key: str) -> str:
    return os.path.join(MODELS_DIR, disease_key, "metrics.json")


def has_trained_classical_model(disease_key: str) -> bool:
    return os.path.isfile(_metrics_path(disease_key))


@lru_cache(maxsize=None)
def load_metrics(disease_key: str) -> Optional[Dict[str, Any]]:
    path = _metrics_path(disease_key)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def model_status_for(disease_key: str) -> str:
    metrics = load_metrics(disease_key)
    if metrics is None:
        return "not_trained"
    if metrics.get("quantum_model"):
        return "classical_and_quantum"
    return "classical_only"


def all_trained_diseases_metrics() -> Dict[str, Dict[str, Any]]:
    if not os.path.isdir(MODELS_DIR):
        return {}
    result = {}
    for entry in sorted(os.listdir(MODELS_DIR)):
        metrics = load_metrics(entry)
        if metrics is not None:
            result[entry] = metrics
    return result
