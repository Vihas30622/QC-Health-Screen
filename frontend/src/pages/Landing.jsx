import "../styles/landing.css";

export default function Landing({ onStart }) {
  return (
    <div className="landing">
      <header className="landing-hero">
        <div className="landing-hero-inner">
          <p className="landing-eyebrow">Quick health check</p>
          <h1 className="landing-title">Screen for health risks in a few minutes</h1>
          <p className="landing-sub">
            Share a few basic details about your health, then see which conditions
            may deserve a closer look. No lab results are needed to begin.
          </p>

          <div className="landing-actions">
            <button className="btn-primary" onClick={onStart}>
              Start screening
            </button>
          </div>

          <p className="landing-microcopy">
            Free · Private · Not a diagnosis
          </p>
        </div>
      </header>

      <section className="landing-section landing-flow">
        <h2 className="section-heading">How it works</h2>
        <ol className="flow-list">
          <li>Answer a short health profile with your age, body measurements, and basics.</li>
          <li>Get a first-pass risk view for diabetes, heart disease, and kidney disease.</li>
          <li>Answer a few follow-up questions for anything that needs a closer look.</li>
          <li>Review the final report and the main risk factors.</li>
        </ol>
      </section>

      <section className="landing-section">
        <h2 className="section-heading">A simple, guided process</h2>
        <div className="how-grid">
          <div className="how-item">
            <span className="how-index">1</span>
            <p>Basic profile</p>
            <p>Quick personal and health questions.</p>
          </div>
          <div className="how-item">
            <span className="how-index">2</span>
            <p>Initial screening</p>
            <p>See the first risk estimates across conditions.</p>
          </div>
          <div className="how-item">
            <span className="how-index">3</span>
            <p>Report</p>
            <p>Review the final results and recommendations.</p>
          </div>
        </div>
      </section>

      <section className="disclaimer">
        <p>
          <strong>This is not a diagnosis.</strong> This tool offers experimental
          health-risk estimates and should not replace professional medical advice.
          If you have urgent symptoms, contact a healthcare provider.
        </p>
      </section>
    </div>
  );
}
