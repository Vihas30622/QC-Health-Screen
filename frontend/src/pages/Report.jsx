import { useEffect, useState } from "react";
import { getReport, ApiError } from "../api";
import { riskTone, actionGuidance } from "../utils/risk";
import "../styles/profile-page.css";
import "../styles/results.css";

function formatGeneratedAt(date) {
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function summarize(diseaseReports) {
  const total = diseaseReports.length;
  const checked = diseaseReports.filter(
    (r) => r.status === "predicted" || r.status === "insufficient_information"
  ).length;
  const flagged = diseaseReports.filter(
    (r) => r.status === "predicted" && riskTone(r.risk_probability) !== "low"
  ).length;

  let flagText = "";
  if (checked === 0) {
    flagText = "";
  } else if (flagged === 0) {
    flagText = " — nothing flagged for follow-up";
  } else {
    flagText = ` — ${flagged} flagged for follow-up`;
  }

  return `${checked} of ${total} condition${total === 1 ? "" : "s"} checked${flagText}`;
}

export default function Report({ sessionId, onRestart, onViewModels, onViewHowItWorks }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [generatedAt] = useState(() => new Date());

  useEffect(() => {
    getReport(sessionId)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the report."));
  }, [sessionId]);

  const diseaseReports = report?.disease_reports || [];

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <h1 className="profile-title">Health screening report</h1>
        <p className="profile-intro report-print-meta">
          Generated {formatGeneratedAt(generatedAt)}
        </p>
        <p className="profile-intro">
          A summary of every condition assessed this session. Percentages
          reflect how common the condition was among similar profiles in
          the data this tool learned from — they're a pointer for what to
          check with a doctor, not a diagnosis.
        </p>

        {error && <p className="form-submit-error">{error}</p>}

        {report && diseaseReports.length > 0 && (
          <div className="report-summary-banner">{summarize(diseaseReports)}</div>
        )}

        {report &&
          diseaseReports.map((entry) => {
            const tone = entry.status === "predicted" ? riskTone(entry.risk_probability) : null;
            const guidance = tone ? actionGuidance(tone) : null;
            return (
              <div
                key={entry.disease_key || entry.display_name}
                className={`report-row${tone ? ` report-row--${tone}` : ""}`}
              >
                <h2 className="form-section-title">{entry.display_name}</h2>
                {entry.status === "not_yet_assessed" && (
                  <p className="form-section-desc">Not yet assessed this session.</p>
                )}
                {entry.status === "insufficient_information" && (
                  <p className="form-section-desc">
                    A couple more details would be needed for this one, usually
                    from a lab report: {entry.missing_information?.join(", ")}
                  </p>
                )}
                {entry.status === "predicted" && (
                  <>
                    <p className="report-row-result">
                      {Math.round(entry.risk_probability * 100)}% — {entry.risk_label}
                    </p>
                    {guidance && <p className="report-row-guidance">{guidance}</p>}
                  </>
                )}
              </div>
            );
          })}

        {report && <p className="disclaimer-inline">{report.disclaimer}</p>}

        <div className="form-actions no-print">
          <button className="btn-secondary" onClick={() => window.print()}>
            Print / save as PDF
          </button>
          <button className="btn-secondary" onClick={onViewModels}>
            See the technical details
          </button>
          <button className="btn-secondary" onClick={onViewHowItWorks}>
            How the quantum model works
          </button>
          <button className="btn-primary" onClick={onRestart}>
            Start a new session
          </button>
        </div>
      </div>
    </div>
  );
}
