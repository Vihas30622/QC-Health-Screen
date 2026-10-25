# Builds and serves the whole app (UI + API) as a single container.
#
# Build:  docker build -t quantum-health-screening .
# Run:    docker run -p 8000:8000 quantum-health-screening
# Then open http://localhost:8000
#
# This is the recommended way to deploy: push this image (or point a
# platform like Render/Railway/Fly.io/Cloud Run at this repo) and you
# get one URL serving both the React UI and the FastAPI backend, with
# no separate static host, no CORS setup, and no VITE_API_BASE to
# manage — the frontend is built with API calls pointed at its own
# origin (see the empty VITE_API_BASE build-arg below).

# ---- Stage 1: build the frontend -----------------------------------
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty string -> the frontend calls the API with relative paths, i.e.
# the same origin it's served from. No cross-origin requests needed.
ENV VITE_API_BASE=""
RUN npm run build

# ---- Stage 2: the actual app -----------------------------------------
FROM python:3.11-slim AS runtime
WORKDIR /app

# System deps for scikit-learn/numpy wheels are already covered by
# manylinux wheels on this base image, so no extra apt packages needed.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY models/ models/
COPY --from=frontend-build /app/frontend/dist/ frontend/dist/

# Most hosts (Render, Railway, Fly.io, Cloud Run) inject $PORT; default
# to 8000 for a plain `docker run` locally.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
