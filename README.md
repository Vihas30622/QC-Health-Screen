# Quantum Health Screening

A web application that estimates risk for diabetes, heart disease, and kidney
disease using trained machine-learning models.

> **Important:** This is a research screening tool, not a medical diagnosis.
> It does not replace a doctor or other qualified healthcare professional.

## What the app does

1. Collects a basic health profile, with metric or imperial height and
   weight entry.
2. Gives an initial risk estimate for three conditions.
3. Asks optional disease-specific follow-up questions.
4. Produces a report with risk estimates and contributing factors.
5. Shows model metrics and technical details.
6. Can import supported values from a structured medical-report QR code.

The backend keeps screening sessions in memory for up to 30 minutes. It does
not use a database or permanently store names, emails, or raw QR payloads.

## Requirements

- Python 3.11
- Node.js 20 or newer
- npm

Docker is also supported and is the easiest option for a single-container
deployment.

## Run locally

Open two terminals from the project root.

### 1. Install and run the backend

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Backend URLs:

- App API: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Install and run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

The frontend expects the backend at `http://localhost:8000`. To use another
backend URL, copy `frontend/.env.example` to `frontend/.env` and update
`VITE_API_BASE`.

## Deploy the frontend to GitHub Pages

This repository keeps the React/Vite app in `frontend/` and the Python API,
ML pipeline, datasets, and model files at the repository root. GitHub Pages
can host only the static frontend; it cannot run the API or model inference.
The existing Actions workflow builds `frontend/` and deploys only
`frontend/dist/`, so the monorepo does not need to be rearranged into a
root-level Pages layout or a `docs/` folder.

To publish a working screening app:

1. Deploy the backend separately to a public HTTPS host using the Dockerfile
   or the local backend instructions above.
2. In the repository's **Settings → Secrets and variables → Actions →
   Variables**, create `VITE_API_BASE` with the backend's HTTPS origin (for
   example, `https://api.example.com`, without a trailing slash).
3. Configure the backend's `ALLOWED_ORIGINS` environment variable to include
   the exact GitHub Pages site origin (for example,
   `https://<owner>.github.io`). The backend must allow browser requests from
   that origin.
4. In **Settings → Pages**, select **GitHub Actions** as the build and
   deployment source. Push a change to `main` under `frontend/` or run
   **Deploy frontend to GitHub Pages** manually from the Actions tab.

The Vite config uses relative asset URLs, which work both at a project site
such as `https://<owner>.github.io/<repository>/` and at a user/org site.
Without `VITE_API_BASE`, the static UI can still be published, but screening
API features will not work because GitHub Pages does not host the backend.

## Required profile data

The first screening requires:

- Age: 1 to 120 years
- Biological sex
- Height: 50 to 250 cm
- Weight: 2 to 400 kg
- Smoking status
- Alcohol consumption
- Physical activity level

Optional profile data includes:

- Systolic and diastolic blood pressure
- Resting heart rate
- Family history
- Existing conditions
- Current symptoms

Height and weight are used to calculate BMI. The API rejects implausible BMI
values and requires diastolic blood pressure to be lower than systolic blood
pressure when both are supplied.

## Medical report QR import

The profile page supports two ways to import report data:

- Scan a QR code with a supported browser camera API.
- Paste the decoded QR text when camera scanning is unavailable.

The QR code must contain structured JSON. Imported values are displayed for
review before they are added to the screening. Unsupported fields, names, and
patient identifiers are ignored.

Example:

```json
{
  "patient": {
    "age": 52,
    "biological_sex": "female",
    "height_cm": 168,
    "weight_kg": 74
  },
  "measurements": {
    "glucose": 110,
    "cholesterol": 190,
    "serum_creatinine": 1.1
  }
}
```

QR values are validated by the backend and passed through the same feature
resolution path as manually entered follow-up values. Missing clinical values
can still produce an `insufficient_information` result.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Check that the API is running |
| GET | `/diseases` | List supported diseases |
| POST | `/screening/basic` | Validate and create a screening session |
| POST | `/screening/import-report` | Validate QR report JSON without storing raw data |
| POST | `/screening/initial` | Run the initial multi-disease screen |
| GET | `/screening/followup/{disease}` | Get follow-up questions |
| POST | `/screening/followup` | Save follow-up answers |
| POST | `/prediction/{disease}` | Run a disease-specific prediction |
| GET | `/screening/report/{session_id}` | Get the combined report |
| GET | `/models` | Get stored model metrics |
| GET | `/circuit/{disease}` | Get the quantum circuit or an unavailable response |

## Test and build

Run the backend and ML tests:

```bash
python -m pytest backend/tests ml/tests -q
```

Compile Python modules:

```bash
python -m compileall -q backend ml
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Train the models

Training dependencies are listed separately:

```bash
python -m pip install -r ml/requirements.txt
python -m ml.training.train_disease all
```

The training pipeline writes model files and metrics under `models/`. The
backend only loads those files; it does not train models while serving users.

## Docker

Build and run the complete application as one service:

```bash
docker build -t quantum-health-screening .
docker run -p 8000:8000 quantum-health-screening
```

Open http://localhost:8000.

## Project structure

```text
backend/       FastAPI API, validation, sessions, and predictions
frontend/      React/Vite user interface
ml/            Dataset loaders, preprocessing, training, and evaluation
datasets/      Source datasets
models/        Trained model artifacts and metrics
docs/          Detailed architecture and research notes
```

For dataset details, model design, limitations, and research background, see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
