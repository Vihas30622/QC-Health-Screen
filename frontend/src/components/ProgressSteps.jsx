import "../styles/progress.css";

const STEPS = [
  "Basic profile",
  "Initial screening",
  "Targeted questions",
  "Results",
];

export default function ProgressSteps({ currentIndex }) {
  return (
    <ol className="progress-steps" aria-label="Screening progress">
      {STEPS.map((label, i) => {
        const state =
          i < currentIndex ? "done" : i === currentIndex ? "active" : "upcoming";
        return (
          <li key={label} className={`progress-step progress-step--${state}`}>
            <span className="progress-step-marker" aria-hidden="true">
              {state === "done" ? "✓" : i + 1}
            </span>
            <span className="progress-step-label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
