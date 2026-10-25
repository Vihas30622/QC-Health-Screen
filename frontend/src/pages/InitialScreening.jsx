import ProgressSteps from "../components/ProgressSteps";
import "../styles/profile-page.css";
import "../styles/initial-screening.css";

function riskTone(probability) {
  if (probability == null) return "unknown";
  if (probability >= 0.6) return "high";
  if (probability >= 0.35) return "moderate";
  return "low";
}

export default function InitialScreening({ results, onBackToHome, onSelectDisease, onSkipToReport }) {
  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <ProgressSteps currentIndex={1} />
        <h1 className="profile-title">Initial screening</h1>
        <p className="profile-intro">
          Based on your basic profile alone, so treat these numbers as a
          rough first pass. Pick a condition below to answer a few more
          targeted questions and get a fuller estimate.
        </p>

        <div className="screening-table-wrap">
          <table className="screening-table">
            <thead>
              <tr>
                <th>Condition</th>
                <th>Initial risk</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.disease_key}>
                  <td>{r.display_name}</td>
                  <td className="risk-cell">
                    {r.risk_probability != null
                      ? `${Math.round(r.risk_probability * 100)}%`
                      : "—"}
                  </td>
                  <td>
                    <span className={`risk-pill risk-pill--${riskTone(r.risk_probability)}`}>
                      {r.status_label}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn-link"
                      onClick={() => onSelectDisease(r.disease_key)}
                      disabled={r.risk_probability == null}
                    >
                      Continue →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="screening-caption">
          This estimates which conditions may warrant a closer look — it
          is not a diagnosis.
        </p>

        <div className="form-actions">
          <button className="btn-secondary" onClick={onBackToHome}>
            ← Home
          </button>
          <button className="btn-secondary" onClick={onSkipToReport}>
            Skip to report
          </button>
        </div>
      </div>
    </div>
  );
}
