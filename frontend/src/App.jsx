import { useEffect, useState } from "react";
import Landing from "./pages/Landing";
import BasicProfile from "./pages/BasicProfile";
import InitialScreening from "./pages/InitialScreening";
import Followup from "./pages/Followup";
import Results from "./pages/Results";
import Report from "./pages/Report";
import ModelComparison from "./pages/ModelComparison";
import HowItWorks from "./pages/HowItWorks";
import { runInitialScreening } from "./api";

const VIEWS = {
  LANDING: "landing",
  PROFILE: "profile",
  LOADING_SCREENING: "loading_screening",
  SCREENING: "screening",
  FOLLOWUP: "followup",
  RESULTS: "results",
  REPORT: "report",
  MODELS: "models",
  HOW_IT_WORKS: "how_it_works",
};

// Persisting just enough of the session to survive an accidental
// refresh or back-button tap. The backend session (created once the
// basic profile is submitted) lives for 30 minutes of inactivity, so
// re-hydrating this on load and re-fetching from the same session_id
// picks up right where things left off, without storing anything new
// on the server. LOADING_SCREENING is deliberately never persisted —
// reloading mid-request should land somewhere stable, not stuck.
const STORAGE_KEY = "qhs_session_v1";

function loadPersistedState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const persisted = loadPersistedState();

export default function App() {
  const [view, setView] = useState(persisted?.view || VIEWS.LANDING);
  const [sessionId, setSessionId] = useState(persisted?.sessionId || null);
  const [screeningResults, setScreeningResults] = useState(persisted?.screeningResults || null);
  const [selectedDisease, setSelectedDisease] = useState(persisted?.selectedDisease || null);
  const [currentResult, setCurrentResult] = useState(persisted?.currentResult || null);
  const [screeningError, setScreeningError] = useState(null);

  useEffect(() => {
    if (view === VIEWS.LOADING_SCREENING) return;
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ view, sessionId, screeningResults, selectedDisease, currentResult })
      );
    } catch {
      // sessionStorage unavailable (private browsing, quota, etc.) —
      // the app still works, it just won't survive a refresh.
    }
  }, [view, sessionId, screeningResults, selectedDisease, currentResult]);

  const clearPersistedState = () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  };

  const goToScreening = async (sid) => {
    setScreeningResults(null);
    setScreeningError(null);
    setView(VIEWS.LOADING_SCREENING);
    try {
      const res = await runInitialScreening(sid);
      setScreeningResults(res.results);
      setView(VIEWS.SCREENING);
    } catch (err) {
      setScreeningError(err.message || "Could not run initial screening.");
      setView(VIEWS.SCREENING);
    }
  };

  if (view === VIEWS.PROFILE) {
    return (
      <BasicProfile
        onBackToHome={() => {
          clearPersistedState();
          setSessionId(null);
          setScreeningResults(null);
          setSelectedDisease(null);
          setCurrentResult(null);
          setView(VIEWS.LANDING);
        }}
        onSubmitted={(res) => {
          setSessionId(res.session_id);
          goToScreening(res.session_id);
        }}
      />
    );
  }

  if (view === VIEWS.LOADING_SCREENING) {
    return (
      <div className="profile-page">
        <div className="profile-page-inner">
          <p className="profile-intro">Running initial screening…</p>
        </div>
      </div>
    );
  }

  if (view === VIEWS.SCREENING && screeningResults) {
    return (
      <div>
        {screeningError && (
          <div className="profile-page">
            <div className="profile-page-inner">
              <p className="form-submit-error">{screeningError}</p>
            </div>
          </div>
        )}
        <InitialScreening
          results={screeningResults}
          onBackToHome={() => {
            clearPersistedState();
            setSessionId(null);
            setScreeningResults(null);
            setSelectedDisease(null);
            setCurrentResult(null);
            setView(VIEWS.LANDING);
          }}
          onSelectDisease={(key) => {
            setSelectedDisease(key);
            setView(VIEWS.FOLLOWUP);
          }}
          onSkipToReport={() => setView(VIEWS.REPORT)}
        />
      </div>
    );
  }

  if (view === VIEWS.SCREENING) {
    return (
      <div className="profile-page">
        <div className="profile-page-inner">
          <p className="form-submit-error" role="alert">
            {screeningError || "The initial screening did not finish. Try again."}
          </p>
          <div className="form-actions">
            <button
              className="btn-secondary"
              onClick={() => {
                clearPersistedState();
                setSessionId(null);
                setScreeningResults(null);
                setSelectedDisease(null);
                setCurrentResult(null);
                setView(VIEWS.LANDING);
              }}
            >
              ← Home
            </button>
            <button className="btn-primary" onClick={() => goToScreening(sessionId)}>
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (view === VIEWS.FOLLOWUP && selectedDisease) {
    const diseaseName =
      screeningResults?.find((r) => r.disease_key === selectedDisease)?.display_name ||
      selectedDisease;
    return (
      <Followup
        sessionId={sessionId}
        diseaseKey={selectedDisease}
        diseaseName={diseaseName}
        onBackToHome={() => {
          clearPersistedState();
          setSessionId(null);
          setScreeningResults(null);
          setSelectedDisease(null);
          setCurrentResult(null);
          setView(VIEWS.LANDING);
        }}
        onDone={(result) => {
          setCurrentResult(result);
          setView(VIEWS.RESULTS);
        }}
      />
    );
  }

  if (view === VIEWS.RESULTS && currentResult) {
    return (
      <Results
        result={currentResult}
        onBackToScreening={() => setView(VIEWS.SCREENING)}
        onDone={() => setView(VIEWS.REPORT)}
      />
    );
  }

  if (view === VIEWS.REPORT && sessionId) {
    return (
      <Report
        sessionId={sessionId}
        onViewModels={() => setView(VIEWS.MODELS)}
        onViewHowItWorks={() => setView(VIEWS.HOW_IT_WORKS)}
        onRestart={() => {
          clearPersistedState();
          setSessionId(null);
          setScreeningResults(null);
          setSelectedDisease(null);
          setCurrentResult(null);
          setView(VIEWS.LANDING);
        }}
      />
    );
  }

  if (view === VIEWS.MODELS) {
    return (
      <div>
        <ModelComparison onBack={() => setView(sessionId ? VIEWS.REPORT : VIEWS.LANDING)} />
      </div>
    );
  }

  if (view === VIEWS.HOW_IT_WORKS) {
    return <HowItWorks onBack={() => setView(sessionId ? VIEWS.REPORT : VIEWS.LANDING)} />;
  }

  return <Landing onStart={() => setView(VIEWS.PROFILE)} />;
}
