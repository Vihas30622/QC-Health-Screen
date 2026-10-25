export const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/+$/, "");
export const API_PREFIX = "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// FastAPI/pydantic validation errors arrive as a list of {loc, msg} objects
// when detail comes straight from a 422. Flatten that into readable text.
function formatDetail(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return String(detail);
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = (body && (body.detail || body.message)) || `Request failed with status ${res.status}`;
    throw new ApiError(formatDetail(detail), res.status);
  }
  return body;
}

export function submitBasicProfile(profile) {
  return request("/screening/basic", { method: "POST", body: JSON.stringify(profile) });
}

export function importReportQr(qrPayload) {
  return request("/screening/import-report", {
    method: "POST",
    body: JSON.stringify({ qr_payload: qrPayload }),
  });
}

export function runInitialScreening(sessionId) {
  return request("/screening/initial", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export function getFollowupQuestions(diseaseKey) {
  return request(`/screening/followup/${diseaseKey}`);
}

export function submitFollowupAnswers(sessionId, diseaseKey, answers) {
  return request("/screening/followup", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, disease_key: diseaseKey, answers }),
  });
}

export function getPrediction(diseaseKey, sessionId) {
  return request(`/prediction/${diseaseKey}`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export function getReport(sessionId) {
  return request(`/screening/report/${sessionId}`);
}

export function getModels() {
  return request("/models");
}

export function getCircuitDiagram(diseaseKey) {
  return request(`/circuit/${diseaseKey}`);
}
