from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class FollowupQuestionsResponse(BaseModel):
    disease_key: str
    questions: List[Dict[str, Any]]


class FollowupAnswersRequest(BaseModel):
    session_id: str
    disease_key: str
    answers: Dict[str, Any]


class FollowupAnswersResponse(BaseModel):
    session_id: str
    disease_key: str
    still_missing: List[str]


class InitialScreeningRequest(BaseModel):
    session_id: str


class InitialScreeningItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    disease_key: str
    display_name: str
    risk_probability: Optional[float]
    status_label: str
    model_used: str
    note: Optional[str] = None


class InitialScreeningResponse(BaseModel):
    session_id: str
    results: List[InitialScreeningItem]
    disclaimer: str


class PredictionRequest(BaseModel):
    session_id: str


class ContributingFactor(BaseModel):
    label: str
    importance: float


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    disease_key: str
    status: str  # "predicted" | "insufficient_information"
    risk_probability: Optional[float] = None
    risk_label: Optional[str] = None
    model_used: Optional[str] = None
    model_metrics: Optional[Dict[str, Any]] = None
    contributing_factors: Optional[List[ContributingFactor]] = None
    missing_information: Optional[List[str]] = None
    disclaimer: str
