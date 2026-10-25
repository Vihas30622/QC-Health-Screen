import { useEffect, useState } from "react";
import { getCircuitDiagram, ApiError } from "../api";
import "../styles/profile-page.css";

export default function HowItWorks({ onBack }) {
  const [diagram, setDiagram] = useState(null);
  const [unavailable, setUnavailable] = useState(null);

  useEffect(() => {
    getCircuitDiagram("diabetes")
      .then((res) => setDiagram(res.diagram_text))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 501) {
          setUnavailable(err.message);
        } else {
          setUnavailable("Could not load the circuit diagram.");
        }
      });
  }, []);

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <h1 className="profile-title">How the quantum model works</h1>
        <p className="profile-intro">
          Each disease's features are reduced to a small number of qubits
          via PCA, angle-encoded into rotation gates, then run through a
          trained variational circuit on a simulator. This is the actual
          circuit structure used, not an illustration.
        </p>

        {diagram && <pre className="circuit-diagram-text">{diagram}</pre>}
        {unavailable && <p className="form-submit-error">{unavailable}</p>}

        <button className="btn-secondary" onClick={onBack}>
          ← Back
        </button>
      </div>
    </div>
  );
}
