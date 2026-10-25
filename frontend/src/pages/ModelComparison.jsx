import { useEffect, useState } from "react";
import { API_BASE, API_PREFIX, getModels, ApiError } from "../api";
import "../styles/profile-page.css";
import "../styles/model-comparison.css";

const METRIC_LABELS = { accuracy: "Accuracy", f1: "F1", roc_auc: "ROC-AUC" };

function Bar({ label, value, max = 1 }) {
  return (
    <div className="metric-bar-row">
      <span className="metric-bar-label">{label}</span>
      <span className="metric-bar-track">
        <span className="metric-bar-fill" style={{ width: `${(value / max) * 100}%` }} />
      </span>
      <span className="metric-bar-value">{value != null ? value.toFixed(3) : "—"}</span>
    </div>
  );
}

export default function ModelComparison({ onBack }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getModels()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load model metrics."));
  }, []);

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <h1 className="profile-title">Model comparison</h1>
        <p className="profile-intro">
          Real evaluation metrics from the last training run — nothing
          here is estimated or assumed. Classical and quantum models are
          compared, not ranked as one being inherently better.
        </p>

        {error && <p className="form-submit-error">{error}</p>}

        {data &&
          Object.entries(data).map(([diseaseKey, disease]) => (
            <section key={diseaseKey} className="comparison-section">
              <h2 className="form-section-title">{disease.display_name}</h2>
              <p className="form-section-desc">
                {disease.n_samples} samples · {disease.n_features} raw features ·{" "}
                {(disease.positive_rate * 100).toFixed(1)}% positive rate
              </p>

              {Object.entries(disease.classical_models).map(([modelName, m]) => (
                <div key={modelName} className="model-block">
                  <p className="model-block-title">{modelName.replace(/_/g, " ")}</p>
                  <Bar label="Accuracy" value={m.accuracy} />
                  <Bar label="F1" value={m.f1} />
                  {m.roc_auc != null && <Bar label="ROC-AUC" value={m.roc_auc} />}
                  <p className="model-block-meta">
                    train: {m.training_time_sec}s · inference: {m.inference_time_sec * 1000}ms/sample
                  </p>
                  <div className="chart-thumbs">
                    <img
                      className="chart-thumb"
                      alt={`${modelName} confusion matrix`}
                      src={`${API_BASE}${API_PREFIX}/models/${diseaseKey}/charts/confusion_${modelName}.png`}
                      onError={(e) => { e.target.style.display = "none"; }}
                    />
                    <img
                      className="chart-thumb"
                      alt={`${modelName} ROC curve`}
                      src={`${API_BASE}${API_PREFIX}/models/${diseaseKey}/charts/roc_${modelName}.png`}
                      onError={(e) => { e.target.style.display = "none"; }}
                    />
                  </div>
                </div>
              ))}

              <img
                className="chart-full"
                alt={`${disease.display_name} model comparison`}
                src={`${API_BASE}${API_PREFIX}/models/${diseaseKey}/charts/model_comparison.png`}
                onError={(e) => { e.target.style.display = "none"; }}
              />

              {disease.quantum_model ? (
                <div className="model-block model-block--quantum">
                  <p className="model-block-title">vqc (quantum)</p>
                  <Bar label="Accuracy" value={disease.quantum_model.accuracy} />
                  <Bar label="F1" value={disease.quantum_model.f1} />
                  <p className="model-block-meta">
                    {disease.quantum_model.n_qubits} qubits ·{" "}
                    {disease.quantum_model.circuit_layers} circuit layers ·{" "}
                    {disease.quantum_model.simulator}
                  </p>
                </div>
              ) : (
                <p className="model-block-meta model-block-meta--muted">
                  No quantum model trained yet for this disease.
                </p>
              )}
            </section>
          ))}

        <button className="btn-secondary" onClick={onBack}>
          ← Back
        </button>
      </div>
    </div>
  );
}
