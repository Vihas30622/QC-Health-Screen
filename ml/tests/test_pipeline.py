"""
Tests for the ML pipeline: dataset loaders, missing-value handling,
scaling, and evaluation. Run with:

    pytest ml/tests -v      (from the project root)
"""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from ml.common.dataset import load_dataset, load_diabetes, load_heart, load_kidney
from ml.common.evaluation import fit_and_evaluate
from ml.common.preprocessor import DiseasePreprocessor


def test_load_diabetes_shape_and_labels():
    ds = load_diabetes()
    assert ds.X.shape[0] == ds.y.shape[0]
    assert ds.X.shape[1] == len(ds.feature_names)
    assert set(np.unique(ds.y)).issubset({0, 1})


def test_load_heart_shape_and_labels():
    ds = load_heart()
    assert ds.X.shape[0] == ds.y.shape[0]
    assert ds.X.shape[1] == len(ds.feature_names)
    assert set(np.unique(ds.y)).issubset({0, 1})


def test_load_kidney_shape_and_labels():
    ds = load_kidney()
    assert ds.X.shape[0] == ds.y.shape[0] == 158
    assert ds.X.shape[1] == len(ds.feature_names) == 24
    assert set(np.unique(ds.y)).issubset({0, 1})


def test_load_dataset_unknown_key_raises():
    with pytest.raises(KeyError):
        load_dataset("liver")  # no dataset sourced for this one — must not silently fabricate one


def test_quantum_encoding_pipeline_shapes_and_bounds():
    from ml.quantum.dimensionality_reduction import QuantumEncodingPipeline

    rng = np.random.default_rng(0)
    X = rng.normal(size=(50, 8))

    enc = QuantumEncodingPipeline(n_qubits=4)
    X_train_q = enc.fit_transform(X[:35])
    X_test_q = enc.transform(X[35:])

    assert X_train_q.shape == (35, 4)
    assert X_test_q.shape == (15, 4)
    # small tolerance for floating-point noise at the exact bounds
    assert X_train_q.min() >= -1e-9
    assert X_train_q.max() <= np.pi + 1e-9
    assert len(enc.explained_variance_ratio) == 4


def test_quantum_encoding_pipeline_caps_qubits_to_available_features():
    from ml.quantum.dimensionality_reduction import QuantumEncodingPipeline

    rng = np.random.default_rng(0)
    X = rng.normal(size=(35, 8))
    enc = QuantumEncodingPipeline(n_qubits=10)  # more than the 8 raw features
    enc.fit_transform(X)
    assert enc.n_components == 8


def test_generate_disease_charts_writes_real_files(tmp_path):
    from ml.common.charts import generate_disease_charts

    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, size=40)
    y_pred = rng.integers(0, 2, size=40)
    y_proba = rng.random(size=40)

    per_model = {
        "logistic_regression": {"y_true": y_true, "y_pred": y_pred, "y_proba": y_proba},
        "svm": {"y_true": y_true, "y_pred": y_pred, "y_proba": None},  # no predict_proba
    }
    all_results = {
        "logistic_regression": {"accuracy": 0.8, "precision": 0.7, "recall": 0.75, "f1": 0.72},
        "svm": {"accuracy": 0.78, "precision": 0.68, "recall": 0.7, "f1": 0.69},
    }

    written = generate_disease_charts(
        "diabetes", "Diabetes", ["No diabetes", "Diabetes"],
        str(tmp_path), per_model, all_results,
    )
    for path in written:
        assert __import__("os").path.isfile(path)
    # svm had no y_proba -> no ROC curve for it, only confusion matrix
    assert any("confusion_svm" in p for p in written)
    assert not any("roc_svm" in p for p in written)
    assert any("model_comparison" in p for p in written)


def test_preprocessor_treats_sentinel_zero_as_missing_and_imputes():
    feature_names = ["glucose", "age"]
    X_train = np.array([
        [120.0, 30.0],
        [0.0, 40.0],    # sentinel-missing glucose
        [140.0, 50.0],
    ])
    pre = DiseasePreprocessor(feature_names=feature_names, missing_value_columns=["glucose"])
    X_scaled = pre.fit_transform(X_train)

    # The imputed value should be the median of the *non-missing* glucose
    # readings (120, 140) -> 130, not the raw 0.
    imputed_raw_glucose = pre._imputer.transform(
        pre._mark_sentinel_as_nan(np.array([[0.0, 40.0]]))
    )[0][0]
    assert imputed_raw_glucose == pytest.approx(130.0)
    assert X_scaled.shape == X_train.shape


def test_preprocessor_requires_fit_before_transform():
    pre = DiseasePreprocessor(feature_names=["a"], missing_value_columns=[])
    with pytest.raises(RuntimeError):
        pre.transform(np.array([[1.0]]))


def test_fit_and_evaluate_returns_real_metrics_in_valid_ranges():
    rng = np.random.default_rng(0)
    X_train = rng.normal(size=(60, 4))
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)
    X_test = rng.normal(size=(20, 4))
    y_test = (X_test[:, 0] + X_test[:, 1] > 0).astype(int)

    result = fit_and_evaluate(
        LogisticRegression(), "logistic_regression", X_train, y_train, X_test, y_test
    )
    d = result.to_dict()
    for metric in ("accuracy", "precision", "recall", "f1"):
        assert 0.0 <= d[metric] <= 1.0
    assert d["roc_auc"] is None or 0.0 <= d["roc_auc"] <= 1.0
    assert d["training_time_sec"] >= 0
    assert d["inference_time_sec"] >= 0
    assert np.array(d["confusion_matrix"]).shape == (2, 2)
    assert d["n_features"] == 4
