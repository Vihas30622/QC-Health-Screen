"""
api/routes.py
==============
  POST /screening/basic              -> validate + store the basic health profile
  GET  /screening/basic/{session_id} -> fetch a stored profile
  POST /screening/initial            -> Phase 7: coarse multi-disease screen
  GET  /screening/followup/{disease} -> Phase 8: which questions to ask
  POST /screening/followup           -> Phase 8: submit answers for one disease
  POST /prediction/{disease}         -> Phase 6: real classical prediction
  GET  /screening/report/{session_id}-> Phase 13: combined final report
  GET  /diseases                     -> list supported diseases + model status
  GET  /models                       -> real on-disk training metrics
  GET  /health                       -> liveness check
"""

from __future__ import annotations

import logging
import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from backend.core.disease_registry import get_disease, list_diseases
from backend.core.session_store import session_store
from backend.schemas.basic_profile import (
    BasicProfileRequest,
    BasicProfileResponse,
    ReportImportRequest,
    ReportImportResponse,
)
from backend.schemas.diseases import DiseaseInfo, DiseaseListResponse, HealthResponse
from backend.schemas.prediction import (
    FollowupAnswersRequest,
    FollowupAnswersResponse,
    FollowupQuestionsResponse,
    InitialScreeningRequest,
    InitialScreeningResponse,
    PredictionRequest,
    PredictionResponse,
)
from backend.services.model_status import all_trained_diseases_metrics
from backend.services.prediction import predict_disease, run_initial_screening
from backend.services.vitals import categorize_bmi, compute_bmi
from backend.core.feature_spec import resolve_feature_vector

logger = logging.getLogger("quantum_health_screening")

router = APIRouter()

_QR_BASIC_ALIASES = {
    "age": "age",
    "biological_sex": "biological_sex",
    "sex": "biological_sex",
    "height_cm": "height_cm",
    "height": "height_cm",
    "weight_kg": "weight_kg",
    "weight": "weight_kg",
    "systolic_bp": "systolic_bp",
    "systolic_blood_pressure": "systolic_bp",
    "diastolic_bp": "diastolic_bp",
    "diastolic_blood_pressure": "diastolic_bp",
    "resting_heart_rate": "resting_heart_rate",
    "smoking_status": "smoking_status",
    "alcohol_consumption": "alcohol_consumption",
    "activity_level": "activity_level",
    "family_history": "family_history",
    "existing_conditions": "existing_conditions",
    "current_symptoms": "current_symptoms",
}

_QR_MEASUREMENT_ALIASES = {
    "pregnancies": "pregnancies",
    "glucose": "fasting_glucose",
    "fasting_glucose": "fasting_glucose",
    "cholesterol": "cholesterol_mg_dl",
    "cholesterol_mg_dl": "cholesterol_mg_dl",
    "resting_systolic_bp": "resting_systolic_bp",
    "resting_diastolic_bp": "resting_diastolic_bp",
    "fasting_blood_sugar_over_120": "fasting_blood_sugar_over_120",
    "resting_ecg_result": "resting_ecg_result",
    "max_heart_rate_achieved": "max_heart_rate_achieved",
    "exercise_induced_angina": "exercise_induced_angina",
    "st_depression_oldpeak": "st_depression_oldpeak",
    "st_slope": "st_slope",
    "num_major_vessels_fluoroscopy": "num_major_vessels_fluoroscopy",
    "thalassemia_result": "thalassemia_result",
    "urine_specific_gravity": "urine_specific_gravity",
    "urine_albumin": "urine_albumin",
    "urine_sugar": "urine_sugar",
    "urine_rbc": "urine_rbc",
    "urine_pus_cell": "urine_pus_cell",
    "urine_pus_cell_clumps": "urine_pus_cell_clumps",
    "urine_bacteria": "urine_bacteria",
    "random_blood_glucose": "random_blood_glucose",
    "blood_urea": "blood_urea",
    "serum_creatinine": "serum_creatinine",
    "serum_sodium": "serum_sodium",
    "serum_potassium": "serum_potassium",
    "hemoglobin": "hemoglobin",
    "packed_cell_volume": "packed_cell_volume",
    "white_blood_cell_count": "white_blood_cell_count",
    "red_blood_cell_count": "red_blood_cell_count",
}


def _import_qr_payload(raw_payload: str) -> ReportImportResponse:
    try:
        decoded = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="QR code must contain a JSON medical report payload.") from exc
    if not isinstance(decoded, dict):
        raise HTTPException(status_code=422, detail="QR code payload must be a JSON object.")

    containers = [decoded]
    for key in ("patient", "basic_profile", "measurements", "followup_answers"):
        value = decoded.get(key)
        if isinstance(value, dict):
            containers.append(value)

    basic_profile: Dict[str, Any] = {}
    followup_answers: Dict[str, Any] = {}
    ignored_fields = []
    for container in containers:
        for key, value in container.items():
            if key in _QR_BASIC_ALIASES:
                basic_profile[_QR_BASIC_ALIASES[key]] = value
            elif key in _QR_MEASUREMENT_ALIASES:
                followup_answers[_QR_MEASUREMENT_ALIASES[key]] = value
            elif key not in {"patient", "basic_profile", "measurements", "followup_answers"}:
                ignored_fields.append(key)

    if not basic_profile and not followup_answers:
        raise HTTPException(
            status_code=422,
            detail="QR code did not contain supported screening fields.",
        )
    return ReportImportResponse(
        basic_profile=basic_profile,
        followup_answers=followup_answers,
        ignored_fields=sorted(set(ignored_fields)),
        warnings=[
            "Imported values are suggestions from the report and must be reviewed before screening.",
            "Patient names and identifiers are ignored and are not used by the classifier.",
        ],
    )


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/diseases", response_model=DiseaseListResponse, tags=["diseases"])
def get_diseases() -> DiseaseListResponse:
    diseases = [
        DiseaseInfo(
            key=d.key,
            display_name=d.display_name,
            description=d.description,
            model_status=d.model_status,
        )
        for d in list_diseases()
    ]
    return DiseaseListResponse(diseases=diseases)


def _require_session(session_id: str):
    session = session_store.get(session_id)
    if session is None or session.basic_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found, has expired, or has no basic profile yet.",
        )
    return session


@router.post(
    "/screening/basic",
    response_model=BasicProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["screening"],
)
def submit_basic_profile(payload: BasicProfileRequest) -> BasicProfileResponse:
    """Validates and stores the Step 2 basic health profile in a fresh,
    isolated session. No values are invented here — only what the user
    actually submitted is stored."""
    try:
        bmi = compute_bmi(payload.height_cm, payload.weight_kg)
        bmi_category = categorize_bmi(bmi)

        session = session_store.create()
        session.basic_profile = payload.model_dump()

        logger.info("basic_profile_submitted session_id=%s", session.session_id)

        return BasicProfileResponse(
            session_id=session.session_id,
            bmi=bmi,
            bmi_category=bmi_category,
            profile=payload,
        )
    except Exception as exc:  # noqa: BLE001 - convert to a clean HTTP error
        logger.exception("failed to process basic profile submission")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not process basic profile: {exc}",
        ) from exc


@router.post(
    "/screening/import-report",
    response_model=ReportImportResponse,
    tags=["screening"],
)
def import_report(payload: ReportImportRequest) -> ReportImportResponse:
    """Validate a structured QR report payload without storing it."""
    return _import_qr_payload(payload.qr_payload)


@router.get("/screening/basic/{session_id}", tags=["screening"])
def get_basic_profile(session_id: str):
    session = _require_session(session_id)
    bmi = compute_bmi(
        session.basic_profile["height_cm"], session.basic_profile["weight_kg"]
    )
    return {
        "session_id": session.session_id,
        "bmi": bmi,
        "bmi_category": categorize_bmi(bmi),
        "profile": session.basic_profile,
    }


@router.post(
    "/screening/initial",
    response_model=InitialScreeningResponse,
    tags=["screening"],
)
def submit_initial_screening(payload: InitialScreeningRequest) -> InitialScreeningResponse:
    """Section 4: a coarse risk read across every supported disease,
    using only the basic profile — via each disease's lighter,
    profile-only model (see ml/training/train_disease.py), not the full
    lab-feature classifier. Results tell the frontend which diseases are
    worth a targeted follow-up, not a diagnosis."""
    session = _require_session(payload.session_id)
    results = run_initial_screening(session.basic_profile)
    session.initial_screening = results
    return InitialScreeningResponse(
        session_id=session.session_id,
        results=results,
        disclaimer=(
            "This is a coarse first pass based on general health "
            "information only. It estimates which conditions may warrant "
            "further assessment — it is not a diagnosis."
        ),
    )


@router.get(
    "/screening/followup/{disease}",
    response_model=FollowupQuestionsResponse,
    tags=["screening"],
)
def get_followup_questions(disease: str) -> FollowupQuestionsResponse:
    config = get_disease(disease)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown disease '{disease}'.")
    return FollowupQuestionsResponse(
        disease_key=disease,
        questions=config.followup_questions(),
    )


@router.post(
    "/screening/followup",
    response_model=FollowupAnswersResponse,
    tags=["screening"],
)
def submit_followup(payload: FollowupAnswersRequest) -> FollowupAnswersResponse:
    session = _require_session(payload.session_id)
    config = get_disease(payload.disease_key)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown disease '{payload.disease_key}'.",
        )

    session.followup_answers[payload.disease_key] = payload.answers

    _, missing = resolve_feature_vector(
        config.feature_specs, session.basic_profile, payload.answers
    )
    return FollowupAnswersResponse(
        session_id=session.session_id,
        disease_key=payload.disease_key,
        still_missing=missing,
    )


@router.post(
    "/prediction/{disease}",
    response_model=PredictionResponse,
    tags=["prediction"],
)
def get_prediction(disease: str, payload: PredictionRequest) -> PredictionResponse:
    session = _require_session(payload.session_id)
    config = get_disease(disease)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown disease '{disease}'.")

    followup_answers = {
        **session.basic_profile.get("report_measurements", {}),
        **session.followup_answers.get(disease, {}),
    }
    result = predict_disease(disease, session.basic_profile, followup_answers)
    session.disease_predictions[disease] = result
    return PredictionResponse(**result)


@router.get("/screening/report/{session_id}", tags=["screening"])
def get_report(session_id: str):
    """Section 13: the combined final report — whatever's been computed
    so far for this session. Diseases with no prediction yet show up as
    'not yet assessed' rather than being silently omitted, so the
    frontend can tell the difference between 'not run' and 'insufficient
    information.'"""
    session = _require_session(session_id)
    report = []
    for disease in list_diseases():
        prediction = session.disease_predictions.get(disease.key)
        if prediction is None:
            report.append({"disease_key": disease.key, "display_name": disease.display_name, "status": "not_yet_assessed"})
        else:
            report.append({"display_name": disease.display_name, **prediction})
    return {
        "session_id": session.session_id,
        "initial_screening": session.initial_screening,
        "disease_reports": report,
        "disclaimer": (
            "This system provides experimental health-risk estimates using "
            "machine learning and quantum machine learning. It is not a "
            "medical diagnosis and should not replace professional medical advice."
        ),
    }


@router.get("/circuit/{disease}", tags=["quantum"])
def get_circuit_diagram(disease: str):
    """Section 19: lets the UI show the actual quantum circuit used for a
    disease, not a generic illustration. Falls back honestly if qiskit
    isn't installed in this environment (see README) rather than
    fabricating a diagram."""
    config = get_disease(disease)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown disease '{disease}'.")

    try:
        from ml.quantum.circuit import circuit_text_diagram
        from ml.quantum.dimensionality_reduction import DEFAULT_N_QUBITS
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Qiskit is not installed in this environment, so the circuit "
                "diagram can't be rendered. See README for Phase 5 status."
            ),
        )

    diagram = circuit_text_diagram(DEFAULT_N_QUBITS)
    return {"disease_key": disease, "n_qubits": DEFAULT_N_QUBITS, "diagram_text": diagram}


@router.get("/models/{disease}/charts/{filename}", tags=["system"])
def get_chart_image(disease: str, filename: str):
    """Serves the real PNG charts written by ml/training/train_disease.py
    (confusion matrices, ROC curves, model comparison bars). Filenames are
    checked against an explicit allow-list — this must never become a
    generic file server, and must never expose the .joblib model files
    themselves (Section 16 of the spec is explicit about that)."""
    import os

    from fastapi.responses import FileResponse

    config = get_disease(disease)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown disease '{disease}'.")

    allowed_prefixes = ("confusion_", "roc_")
    allowed_exact = {"model_comparison.png"}
    is_allowed = filename in allowed_exact or (
        filename.startswith(allowed_prefixes) and filename.endswith(".png") and "/" not in filename and ".." not in filename
    )
    if not is_allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart not found.")

    models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
    path = os.path.join(models_dir, disease, "charts", filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart not found.")
    return FileResponse(path, media_type="image/png")


@router.get("/models", tags=["system"])
def list_models():
    """Returns the real, on-disk evaluation metrics produced by
    `ml/training/train_disease.py` for every disease that has a trained
    model — actual accuracy/precision/recall/F1/ROC-AUC/confusion-matrix/
    timing numbers, not placeholders."""
    trained = all_trained_diseases_metrics()
    if not trained:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="No models have been trained yet.",
        )
    return trained
