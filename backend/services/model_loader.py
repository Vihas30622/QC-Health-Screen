"""
services/model_loader.py
==========================
Loads whatever `ml/training/train_disease.py` saved to `models/<disease>/`
— joblib model files, the fitted preprocessor, and the initial-screening
bundle. Cached in memory after first load per process, since these files
don't change while the server is running. Never trains anything itself.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


def _disease_dir(disease_key: str) -> str:
    return os.path.join(MODELS_DIR, disease_key)


@lru_cache(maxsize=None)
def load_metrics(disease_key: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(_disease_dir(disease_key), "metrics.json")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def best_classical_model_name(disease_key: str) -> Optional[str]:
    """Picks the classical model with the highest F1 on the held-out test
    split — an objective, already-computed number, not a preference."""
    metrics = load_metrics(disease_key)
    if not metrics or not metrics.get("classical_models"):
        return None
    models = metrics["classical_models"]
    return max(models, key=lambda name: models[name]["f1"])


@lru_cache(maxsize=None)
def load_preprocessor(disease_key: str):
    path = os.path.join(_disease_dir(disease_key), "preprocessor.joblib")
    if not os.path.isfile(path):
        return None
    return joblib.load(path)


@lru_cache(maxsize=None)
def load_classical_model(disease_key: str, model_name: str):
    path = os.path.join(_disease_dir(disease_key), f"{model_name}.joblib")
    if not os.path.isfile(path):
        return None
    return joblib.load(path)


@lru_cache(maxsize=None)
def load_initial_screening_bundle(disease_key: str):
    path = os.path.join(_disease_dir(disease_key), "initial_screening_bundle.joblib")
    if not os.path.isfile(path):
        return None
    return joblib.load(path)
