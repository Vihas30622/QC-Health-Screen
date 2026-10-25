"""
services/prediction.py
========================
Orchestrates Phase 6 (disease-specific prediction) and Phase 7 (initial
multi-disease screening). Both follow the same rule from Section 6 of
the spec: if a required feature is missing and the user hasn't supplied
it, the result is "insufficient information" — never a guess.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.core.disease_registry import DiseaseConfig, get_disease
from backend.core.feature_spec import resolve_feature_vector
from backend.services.model_loader import (
    best_classical_model_name,
    load_classical_model,
    load_initial_screening_bundle,
    load_metrics,
    load_preprocessor,
)

DISCLAIMER = (
    "This is an experimental risk estimate from machine learning and "
    "quantum machine learning models, not a medical diagnosis. It should "
    "not replace professional medical advice."
)


def _risk_label(probability: float) -> str:
    if probability >= 0.6:
        return "Higher estimated risk — further assessment recommended"
    if probability >= 0.35:
        return "Moderate estimated risk — further assessment may be useful"
    return "Lower estimated risk"


def _contributing_factors(
    model, feature_specs, top_n: int = 5
) -> Optional[List[Dict[str, Any]]]:
    """Feature-importance-based explainability (Section 14). Random
    forests expose feature_importances_ directly; linear models expose
    coef_. Neither claims to explain medical causation — just which
    inputs moved this particular model's output the most."""
    labels = [spec.label for spec in feature_specs]

    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        return None

    order = np.argsort(importances)[::-1][:top_n]
    return [
        {"label": labels[i], "importance": round(float(importances[i]), 4)}
        for i in order
    ]


def predict_disease(disease_key: str, profile: Dict[str, Any], followup_answers: Dict[str, Any]) -> Dict[str, Any]:
    disease = get_disease(disease_key)
    if disease is None:
        raise KeyError(f"Unknown disease '{disease_key}'")

    if disease.model_status == "not_trained":
        return {
            "disease_key": disease_key,
            "status": "insufficient_information",
            "missing_information": [f"No trained model exists yet for {disease.display_name}."],
            "disclaimer": DISCLAIMER,
        }

    vector, missing = resolve_feature_vector(disease.feature_specs, profile, followup_answers)
    if vector is None:
        return {
            "disease_key": disease_key,
            "status": "insufficient_information",
            "missing_information": missing,
            "disclaimer": DISCLAIMER,
        }

    model_name = best_classical_model_name(disease_key)
    model = load_classical_model(disease_key, model_name)
    preprocessor = load_preprocessor(disease_key)
    metrics = load_metrics(disease_key)

    X = np.array([vector])
    X_p = preprocessor.transform(X)

    if hasattr(model, "predict_proba"):
        probability = float(model.predict_proba(X_p)[0][1])
    else:
        probability = float(model.predict(X_p)[0])  # 0/1 fallback, no calibrated probability

    factors = _contributing_factors(model, disease.feature_specs)
    model_metrics = metrics["classical_models"][model_name] if metrics else None

    return {
        "disease_key": disease_key,
        "status": "predicted",
        "risk_probability": round(probability, 4),
        "risk_label": _risk_label(probability),
        "model_used": model_name,
        "model_metrics": model_metrics,
        "contributing_factors": factors,
        "disclaimer": DISCLAIMER,
    }


def run_initial_screening(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Section 4's coarse first pass — uses the lighter, profile-only
    model trained in ml/training/train_disease.py, not the full
    disease-specific classifier (which needs lab values the profile
    doesn't have)."""
    from backend.core.disease_registry import list_diseases

    results = []
    for disease in list_diseases():
        bundle = load_initial_screening_bundle(disease.key)
        if bundle is None:
            results.append({
                "disease_key": disease.key,
                "display_name": disease.display_name,
                "risk_probability": None,
                "status_label": "Initial screening not available for this condition yet.",
                "model_used": "none",
                "note": "No lightweight profile-only model has been trained for this disease.",
            })
            continue

        features = bundle["features"]
        raw_values = []
        missing = []
        for f in features:
            val = _extract_profile_feature(f, profile)
            if val is None:
                missing.append(f)
            else:
                raw_values.append(val)

        if missing:
            results.append({
                "disease_key": disease.key,
                "display_name": disease.display_name,
                "risk_probability": None,
                "status_label": "Insufficient information from basic profile.",
                "model_used": "initial_screening_logistic_regression",
                "note": f"Missing: {', '.join(missing)}",
            })
            continue

        X = np.array([raw_values])
        X_p = bundle["preprocessor"].transform(X)
        probability = float(bundle["model"].predict_proba(X_p)[0][1])

        results.append({
            "disease_key": disease.key,
            "display_name": disease.display_name,
            "risk_probability": round(probability, 4),
            "status_label": _risk_label(probability),
            "model_used": "initial_screening_logistic_regression",
            "note": None,
        })
    return results


def _extract_profile_feature(raw_name: str, profile: Dict[str, Any]) -> Optional[float]:
    """Maps the small set of raw feature names used by initial-screening
    bundles back to basic-profile fields. Deliberately narrow — only
    covers what INITIAL_SCREENING_FEATURE_SUBSET in the training script
    actually uses."""
    if raw_name == "age":
        return profile.get("age")
    if raw_name == "bmi":
        h, w = profile.get("height_cm"), profile.get("weight_kg")
        return w / ((h / 100) ** 2) if h and w else None
    if raw_name == "blood_pressure":
        return profile.get("diastolic_bp")
    if raw_name == "trestbps":
        return profile.get("systolic_bp")
    if raw_name == "sex":
        sex = profile.get("biological_sex")
        if sex == "male":
            return 1.0
        if sex == "female":
            return 0.0
        return None
    return None
