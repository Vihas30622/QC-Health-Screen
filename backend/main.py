"""
backend/main.py
================
FastAPI application entrypoint.

Run with:
    uvicorn backend.main:app --reload --port 8000

(run from the `quantum-health-screening/` project root so the `backend.*`
package imports resolve)

Single-deployment mode
-----------------------
If `frontend/dist/` exists (i.e. `npm run build` has been run — the
Dockerfile does this automatically), this app also serves the built
frontend as static files from "/". That means the whole product —
UI and API — can be deployed as one process on one host, with no
separate static hosting and no cross-origin requests to configure.
Build the frontend with `VITE_API_BASE=""` in that case, so it calls
the API with relative paths on the same origin.

If `frontend/dist/` doesn't exist (plain local `uvicorn` dev run without
building the frontend first), "/" falls back to a small JSON status
message instead — nothing breaks, there's just no UI to serve yet.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router as api_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Quantum Multi-Disease Health Screening API",
    description=(
        "Backend for the progressive, multi-disease health-risk screening "
        "system. Combines classical ML and quantum ML baselines. "
        "Not a medical diagnostic tool."
    ),
    version="0.1.0",
)

# Local dev origins for `npm run dev` (Vite on 5173) hitting a separately
# running API, plus anything listed in ALLOWED_ORIGINS (comma-separated)
# for a split frontend/backend deployment. Not needed at all when the
# frontend is served from this same app, below — same-origin requests
# aren't subject to CORS in the first place.
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(_FRONTEND_DIST):
    # Mounted last so it only catches requests the API router above
    # didn't already match. html=True serves index.html for "/".
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
else:

    @app.get("/", tags=["system"])
    def root():
        return {
            "message": "Quantum Multi-Disease Health Screening API",
            "docs": "/docs",
            "note": "No built frontend found at frontend/dist — API only. Run `npm run build` in frontend/ to serve the UI from here too.",
            "disclaimer": (
                "This system provides experimental health-risk estimates using "
                "machine learning and quantum machine learning. It is not a "
                "medical diagnosis and should not replace professional medical "
                "advice."
            ),
        }
