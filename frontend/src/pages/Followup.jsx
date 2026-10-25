import { useEffect, useState } from "react";
import ProgressSteps from "../components/ProgressSteps";
import { NumberField, SelectField } from "../components/FormFields";
import { getFollowupQuestions, submitFollowupAnswers, getPrediction, ApiError } from "../api";
import "../styles/form.css";
import "../styles/profile-page.css";

export default function Followup({ sessionId, diseaseKey, diseaseName, onBackToHome, onDone }) {
  const [questions, setQuestions] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getFollowupQuestions(diseaseKey)
      .then((res) => {
        if (!cancelled) setQuestions(res.questions);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not load questions.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [diseaseKey]);

  const setAnswer = (id) => (value) => setAnswers((a) => ({ ...a, [id]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      // Only send fields the person actually filled in — leaving a
      // question blank means "I don't have this," not zero.
      const nonEmpty = Object.fromEntries(
        Object.entries(answers).filter(([, v]) => v !== "" && v != null)
      );
      await submitFollowupAnswers(sessionId, diseaseKey, nonEmpty);
      const prediction = await getPrediction(diseaseKey, sessionId);
      onDone(prediction);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong submitting your answers.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-page-inner">
          <p className="profile-intro">Loading questions…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <ProgressSteps currentIndex={2} />
        <h1 className="profile-title">{diseaseName}: a few more questions</h1>
        <p className="profile-intro">
          Everything here is optional — leave anything blank if you don't
          have it. Blank answers may mean the estimate comes back as
          "insufficient information" rather than a number, which is
          expected and not an error.
        </p>

        {error && <p className="form-submit-error">{error}</p>}

        <form onSubmit={handleSubmit} noValidate>
          <section className="form-section">
            {questions.map((q) => {
              if (q.type === "select" || q.type === "boolean") {
                return (
                  <SelectField
                    key={q.id}
                    id={q.id}
                    label={q.label}
                    value={answers[q.id] ?? ""}
                    onChange={setAnswer(q.id)}
                    options={q.options || []}
                    hint={q.help_text}
                  />
                );
              }
              return (
                <NumberField
                  key={q.id}
                  id={q.id}
                  label={q.label}
                  unit={q.unit}
                  value={answers[q.id] ?? ""}
                  onChange={setAnswer(q.id)}
                  step={0.1}
                  hint={q.help_text}
                />
              );
            })}
          </section>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onBackToHome}>
              ← Home
            </button>
            <p className="form-actions-note">Nothing here is stored beyond this session.</p>
            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Submitting…" : "Get estimate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
