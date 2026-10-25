"""
ml/training/train_disease.py
==============================
Training pipeline (Section 9 of the spec):

    Dataset -> Data Cleaning / Missing Value Handling -> Train/Test Split
    -> Feature Scaling -> Classical Models -> Evaluation
    -> Save Models + Preprocessors

Quantum model training is added in Phase 5 and slots into this same
pipeline. Run standalone; the web app only ever loads what this script
saves — it never retrains on a prediction request.

Usage:
    python3 -m ml.training.train_disease diabetes
    python3 -m ml.training.train_disease heart
    python3 -m ml.training.train_disease all
"""

from __future__ import annotations

import json
import os
import sys

import joblib
from sklearn.model_selection import train_test_split

from ml.classical.models import build_classical_models
from ml.common.charts import generate_disease_charts
from ml.common.dataset import DATASET_LOADERS, load_dataset
from ml.common.evaluation import fit_and_evaluate
from ml.common.preprocessor import DiseasePreprocessor

RANDOM_STATE = 42
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")

# Which raw dataset columns are realistically available from the Basic
# Health Profile alone (Step 2), before any disease-specific follow-up.
# This drives a SEPARATE, lighter "initial screening" model per disease —
# deliberately not the same model used for the full prediction, because
# that one needs lab/diagnostic-test features the basic profile can't
# supply. Keep this in sync with the profile-sourced FeatureSpecs in
# backend/diseases/<disease>/features.py.
INITIAL_SCREENING_FEATURE_SUBSET = {
    "diabetes": ["bmi", "blood_pressure", "age"],
    "heart": ["age", "sex", "trestbps"],
    "kidney": ["age", "blood_pressure"],
}

# Quantum training runs on a simulator, and VQC training cost scales with
# both circuit depth and dataset size. These caps keep an academic
# prototype's training time reasonable on a laptop; they are a practical
# engineering choice, not a claim about what quantum models need in
# general — documented here rather than left as an unexplained magic
# number.
QUANTUM_MAX_TRAIN_SAMPLES = 150
QUANTUM_MAX_TEST_SAMPLES = 60
QUANTUM_MAXITER = 80


def train_quantum(
    key: str,
    disease_dir: str,
    X_train_p,
    y_train,
    X_test_p,
    y_test,
) -> dict | None:
    try:
        from ml.quantum.dimensionality_reduction import QuantumEncodingPipeline
        from ml.quantum.vqc_model import VQCDiseaseClassifier
    except ImportError as exc:
        print(
            f"  [quantum] Skipping quantum model for '{key}' — qiskit is "
            f"not installed in this environment ({exc}). Install "
            f"ml/requirements.txt's quantum extras and rerun to add it."
        )
        return None

    import joblib
    import numpy as np

    rng = np.random.default_rng(RANDOM_STATE)
    train_idx = rng.choice(
        len(X_train_p), size=min(len(X_train_p), QUANTUM_MAX_TRAIN_SAMPLES), replace=False
    )
    test_idx = rng.choice(
        len(X_test_p), size=min(len(X_test_p), QUANTUM_MAX_TEST_SAMPLES), replace=False
    )
    X_train_sub, y_train_sub = X_train_p[train_idx], y_train[train_idx]
    X_test_sub, y_test_sub = X_test_p[test_idx], y_test[test_idx]

    encoder = QuantumEncodingPipeline()
    X_train_q = encoder.fit_transform(X_train_sub)
    X_test_q = encoder.transform(X_test_sub)

    model = VQCDiseaseClassifier(n_qubits=encoder.n_components, maxiter=QUANTUM_MAXITER)

    print(
        f"  [quantum] Training VQC for '{key}': {encoder.n_components} qubits, "
        f"{len(X_train_sub)} training samples (subset of {len(X_train_p)}), "
        f"maxiter={QUANTUM_MAXITER}. This runs on a statevector simulator "
        f"and may take a while."
    )

    result = fit_and_evaluate(
        model,
        "vqc",
        X_train_q,
        y_train_sub,
        X_test_q,
        y_test_sub,
        extra={
            "n_qubits": encoder.n_components,
            "circuit_layers": model.n_circuit_layers,
            "simulator": "qiskit statevector (local, no real hardware)",
            "explained_variance_ratio": encoder.explained_variance_ratio,
            "train_subset_size": len(X_train_sub),
            "test_subset_size": len(X_test_sub),
            "note": (
                "Trained on a random subset of the full training split "
                "to keep simulator runtime tractable — see "
                "QUANTUM_MAX_TRAIN_SAMPLES in this file."
            ),
        },
    )

    joblib.dump(
        {"encoder": encoder, "model": model},
        os.path.join(disease_dir, "vqc_bundle.joblib"),
    )
    print(
        f"  {'vqc':20s} acc={result.accuracy:.3f} f1={result.f1:.3f} "
        f"roc_auc={result.roc_auc if result.roc_auc is None else round(result.roc_auc, 3)} "
        f"train_time={result.training_time_sec:.3f}s"
    )
    return result.to_dict()


def train_initial_screening_model(
    key: str,
    dataset,
    disease_dir: str,
    X_train_raw,
    y_train,
    X_test_raw,
    y_test,
) -> dict | None:
    """A separate, deliberately lighter model trained only on the columns
    a Basic Health Profile can supply (Section 4's coarse first pass) —
    not the same model used for the full disease-specific prediction in
    Phase 6, which needs lab/diagnostic features the profile doesn't
    have. Its accuracy is expected to be lower than the full model; that
    trade-off is the whole point of a two-stage screen, not a defect."""
    subset = INITIAL_SCREENING_FEATURE_SUBSET.get(key)
    if not subset:
        return None

    from sklearn.linear_model import LogisticRegression

    idx = [dataset.feature_names.index(f) for f in subset]
    X_train_sub = X_train_raw[:, idx]
    X_test_sub = X_test_raw[:, idx]

    sub_preprocessor = DiseasePreprocessor(
        feature_names=subset,
        missing_value_columns=[c for c in dataset.missing_value_columns if c in subset],
    )
    X_train_sub_p = sub_preprocessor.fit_transform(X_train_sub)
    X_test_sub_p = sub_preprocessor.transform(X_test_sub)

    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    result = fit_and_evaluate(
        model, "initial_screening_logistic_regression",
        X_train_sub_p, y_train, X_test_sub_p, y_test,
        extra={"features_used": subset},
    )

    joblib.dump(
        {"model": model, "preprocessor": sub_preprocessor, "features": subset},
        os.path.join(disease_dir, "initial_screening_bundle.joblib"),
    )
    print(
        f"  {'initial_screening':20s} acc={result.accuracy:.3f} f1={result.f1:.3f} "
        f"roc_auc={result.roc_auc if result.roc_auc is None else round(result.roc_auc, 3)} "
        f"features={subset}"
    )
    return result.to_dict()


def train_disease(key: str) -> dict:
    dataset = load_dataset(key)
    print(f"\n=== {dataset.display_name} ({key}) ===")
    print(f"samples={dataset.X.shape[0]} features={dataset.X.shape[1]} "
          f"positive_rate={dataset.y.mean():.3f}")

    X_train, X_test, y_train, y_test = train_test_split(
        dataset.X, dataset.y, test_size=0.25, random_state=RANDOM_STATE,
        stratify=dataset.y,
    )

    preprocessor = DiseasePreprocessor(
        feature_names=dataset.feature_names,
        missing_value_columns=dataset.missing_value_columns,
    )
    X_train_p = preprocessor.fit_transform(X_train)
    X_test_p = preprocessor.transform(X_test)

    disease_dir = os.path.join(MODELS_DIR, key)
    os.makedirs(disease_dir, exist_ok=True)

    model_results = {}
    fitted_models = {}
    for name, model in build_classical_models().items():
        result = fit_and_evaluate(
            model, name, X_train_p, y_train, X_test_p, y_test
        )
        model_results[name] = result.to_dict()
        fitted_models[name] = model
        joblib.dump(model, os.path.join(disease_dir, f"{name}.joblib"))
        print(
            f"  {name:20s} acc={result.accuracy:.3f} f1={result.f1:.3f} "
            f"roc_auc={result.roc_auc if result.roc_auc is None else round(result.roc_auc, 3)} "
            f"train_time={result.training_time_sec:.3f}s"
        )

    charts_dir = os.path.join(disease_dir, "charts")
    per_model_predictions = {}
    for name, model in fitted_models.items():
        y_pred = model.predict(X_test_p)
        y_proba = None
        if hasattr(model, "predict_proba"):
            try:
                y_proba = model.predict_proba(X_test_p)[:, 1]
            except (ValueError, IndexError):
                y_proba = None
        per_model_predictions[name] = {"y_true": y_test, "y_pred": y_pred, "y_proba": y_proba}

    chart_paths = generate_disease_charts(
        key, dataset.display_name, list(dataset.class_names),
        charts_dir, per_model_predictions, model_results,
    )
    print(f"  Wrote {len(chart_paths)} chart(s) to {charts_dir}/")

    joblib.dump(preprocessor, os.path.join(disease_dir, "preprocessor.joblib"))

    quantum_model_metrics = train_quantum(
        key, disease_dir, X_train_p, y_train, X_test_p, y_test
    )

    initial_screening_metrics = train_initial_screening_model(
        key, dataset, disease_dir, X_train, y_train, X_test, y_test
    )

    metrics = {
        "disease_key": key,
        "display_name": dataset.display_name,
        "n_samples": int(dataset.X.shape[0]),
        "n_features": int(dataset.X.shape[1]),
        "feature_names": dataset.feature_names,
        "class_names": list(dataset.class_names),
        "positive_rate": float(dataset.y.mean()),
        "train_test_split": {"train": len(X_train), "test": len(X_test)},
        "classical_models": model_results,
        "quantum_model": quantum_model_metrics,
        "initial_screening_model": initial_screening_metrics,
    }
    with open(os.path.join(disease_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved models + preprocessor + metrics to {disease_dir}/")
    return metrics


def main():
    keys = sys.argv[1:] or ["all"]
    if keys == ["all"]:
        keys = list(DATASET_LOADERS.keys())

    for key in keys:
        if key not in DATASET_LOADERS:
            print(f"Skipping unknown disease '{key}' (no dataset registered).")
            continue
        train_disease(key)


if __name__ == "__main__":
    main()
