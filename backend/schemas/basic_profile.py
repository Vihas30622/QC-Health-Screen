"""
schemas/basic_profile.py
=========================
Request/response models for the Basic Health Profile step (Step 2 of the
user journey). Validation lives here, not in the frontend alone — the API
must never trust client-side checks.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class BiologicalSex(str, Enum):
    male = "male"
    female = "female"
    intersex = "intersex"
    prefer_not_to_say = "prefer_not_to_say"


class SmokingStatus(str, Enum):
    never = "never"
    former = "former"
    current = "current"


class AlcoholConsumption(str, Enum):
    none = "none"
    occasional = "occasional"
    moderate = "moderate"
    heavy = "heavy"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class BasicProfileRequest(BaseModel):
    # --- Demographics ---
    age: int = Field(..., ge=1, le=120, description="Age in years")
    biological_sex: BiologicalSex

    # --- Anthropometrics ---
    height_cm: float = Field(..., ge=50, le=250, description="Height in centimeters")
    weight_kg: float = Field(..., ge=2, le=400, description="Weight in kilograms")

    # --- Vitals ---
    systolic_bp: Optional[int] = Field(
        None, ge=60, le=260, description="Systolic blood pressure, mmHg"
    )
    diastolic_bp: Optional[int] = Field(
        None, ge=30, le=180, description="Diastolic blood pressure, mmHg"
    )
    resting_heart_rate: Optional[int] = Field(
        None, ge=25, le=220, description="Resting heart rate, bpm"
    )

    # --- Lifestyle ---
    smoking_status: SmokingStatus
    alcohol_consumption: AlcoholConsumption
    activity_level: ActivityLevel

    # --- History ---
    family_history: List[str] = Field(
        default_factory=list,
        description="Free-form list of conditions with family history, e.g. 'diabetes'",
    )
    existing_conditions: List[str] = Field(
        default_factory=list,
        description="Conditions the user already knows they have",
    )
    current_symptoms: List[str] = Field(
        default_factory=list,
        description="Basic symptoms selected at intake, e.g. 'fatigue', 'chest_discomfort'",
    )
    report_measurements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Validated disease-specific measurements imported from a report QR code",
    )

    @model_validator(mode="after")
    def _cross_field_checks(self) -> "BasicProfileRequest":
        if self.systolic_bp is not None and self.diastolic_bp is not None:
            if self.diastolic_bp >= self.systolic_bp:
                raise ValueError(
                    "diastolic_bp must be lower than systolic_bp"
                )
        # BMI sanity: catch height/weight combos that are internally valid
        # per-field but produce a physiologically implausible BMI (data
        # entry errors, e.g. cm/inches confusion).
        bmi = self.bmi
        if bmi < 8 or bmi > 60:
            raise ValueError(
                f"height/weight combination produces an implausible BMI ({bmi:.1f}); "
                "please double-check the values"
            )
        return self

    @property
    def bmi(self) -> float:
        height_m = self.height_cm / 100
        return self.weight_kg / (height_m ** 2)


class BasicProfileResponse(BaseModel):
    """Echoes back the stored profile plus derived fields, so the frontend
    never has to recompute BMI itself."""

    session_id: str
    bmi: float
    bmi_category: str
    profile: BasicProfileRequest


class ReportImportRequest(BaseModel):
    qr_payload: str = Field(..., min_length=1, max_length=100_000)


class ReportImportResponse(BaseModel):
    basic_profile: Dict[str, Any]
    followup_answers: Dict[str, Any]
    ignored_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
