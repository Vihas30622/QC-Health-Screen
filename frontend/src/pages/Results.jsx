import { useState } from "react";
import ProgressSteps from "../components/ProgressSteps";
import { riskTone } from "../utils/risk";
import "../styles/profile-page.css";
import "../styles/results.css";

// A short, plain-language read of the number — so a percentage isn't
// left to speak for itself.
function riskExplainer(probability) {
  const outOf100 = Math.round(probability * 100);
  const tone = riskTone(probability);
  if (tone === "high") {
    return `Out of 100 people with a similar health profile, about ${outOf100} were found to have this condition in the data this tool learned from. That's high enough that it's worth bringing up with a doctor, ideally with a blood or urine test to confirm either way.`;
  }
  if (tone === "moderate") {
    return `Out of 100 people with a similar health profile, about ${outOf100} were found to have this condition in the data this tool learned from. That's a moderate signal — not an emergency, but worth mentioning at your next checkup.`;
  }
  return `Out of 100 people with a similar health profile, about ${outOf100} were found to have this condition in the data this tool learned from. That's a low signal based on what you've entered so far.`;
}

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

export default function Results({ result, onBackToScreening, onDone }) {
  const [showTechnical, setShowTechnical] = useState(false);
  const insufficient = result.status === "insufficient_information";

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <ProgressSteps currentIndex={3} />
        <h1 className="profile-title">Result</h1>

        {insufficient ? (
          <div className="result-card result-card--insufficient">
            <h2 className="result-card-title">A couple more details needed</h2>
            <p>
              We can't give you a number yet — this usually means the
              condition needs a blood or urine test value that most
              people don't have handy, not a problem with anything you
              answered.
            </p>
            {result.missing_information && (
              <>
                <p className="result-missing-label">
                  If you have a recent lab report, these values would complete the picture:
                </p>
                <ul className="result-missing-list">
                  {result.missing_information.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        ) : (
          <div className={`result-card result-card--${riskTone(result.risk_probability)}`}>
            <div className="result-headline">
              <span className="result-probability">
                {formatPercent(result.risk_probability)}
              </span>
              <span className="result-label">{result.risk_label}</span>
            </div>

            <p className="result-explainer">{riskExplainer(result.risk_probability)}</p>

            {result.contributing_factors && (
              <div className="result-factors">
                <p className="result-factors-title">What influenced this estimate most</p>
                <ul>
                  {result.contributing_factors.map((f) => (
                    <li key={f.label}>
                      <span className="factor-label">{f.label}</span>
                      <span className="factor-bar-track">
                        <span
                          className="factor-bar-fill"
                          style={{ width: `${Math.min(100, f.importance * 250)}%` }}
                        />
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              type="button"
              className="technical-toggle"
              onClick={() => setShowTechnical((v) => !v)}
              aria-expanded={showTechnical}
            >
              {showTechnical ? "Hide" : "Show"} technical details
            </button>
            {showTechnical && (
              <p className="result-model-note">
                Model used: <code>{result.model_used}</code>
                {result.model_metrics && (
                  <>
                    {" "}
                    · on past test data this model was right about{" "}
                    {Math.round(result.model_metrics.accuracy * 100)}% of the
                    time (F1 score: {result.model_metrics.f1})
                  </>
                )}
              </p>
            )}
          </div>
        )}

        <p className="disclaimer-inline">{result.disclaimer}</p>

        <div className="form-actions">
          <button className="btn-secondary" onClick={onBackToScreening}>
            ← Back to screening
          </button>
          <button className="btn-primary" onClick={onDone}>
            Finish
          </button>
        </div>
      </div>
    </div>
  );
}
