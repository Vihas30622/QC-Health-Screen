"""
Tests for backend/services/model_loader.py: reading real on-disk
artifacts, never training anything itself.
Run with: pytest backend/tests -v
"""

from backend.services.model_loader import (
    best_classical_model_name,
    load_classical_model,
    load_metrics,
    load_preprocessor,
)


def test_load_metrics_returns_real_data_for_trained_disease():
    metrics = load_metrics("diabetes")
    assert metrics is not None
    assert metrics["disease_key"] == "diabetes"
    assert "logistic_regression" in metrics["classical_models"]


def test_load_metrics_returns_none_for_unknown_disease():
    assert load_metrics("liver") is None


def test_best_classical_model_name_picks_highest_f1():
    metrics = load_metrics("diabetes")
    models = metrics["classical_models"]
    expected = max(models, key=lambda name: models[name]["f1"])
    assert best_classical_model_name("diabetes") == expected


def test_load_preprocessor_and_model_round_trip():
    preprocessor = load_preprocessor("diabetes")
    assert preprocessor is not None
    model_name = best_classical_model_name("diabetes")
    model = load_classical_model("diabetes", model_name)
    assert model is not None
    assert hasattr(model, "predict")


def test_load_classical_model_unknown_name_returns_none():
    assert load_classical_model("diabetes", "not_a_real_model") is None


def test_all_three_diseases_have_trained_metrics():
    for key in ("diabetes", "heart", "kidney"):
        assert load_metrics(key) is not None, f"{key} should have metrics.json from training"
