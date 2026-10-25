"""
core/disease_registry.py
=========================
Central registry of supported diseases. This is the abstraction that lets
Section 10 of the spec hold: "additional diseases can be added later
without rewriting the entire application."

`required_features` and `followup_question_ids` are no longer hand-typed
placeholder lists — they're derived directly from each disease's
FEATURE_SPECS (backend/diseases/<name>/features.py), which is the single
source of truth also used to build the raw feature vector for prediction
(Phase 6) and the follow-up question UI (Phase 8). One list, three
consumers, no drift between them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.core.feature_spec import FeatureSpec, followup_questions_for
from backend.diseases.diabetes.features import FEATURE_SPECS as DIABETES_FEATURES
from backend.diseases.heart.features import FEATURE_SPECS as HEART_FEATURES
from backend.diseases.kidney.features import FEATURE_SPECS as KIDNEY_FEATURES
from backend.services.model_status import model_status_for


@dataclass
class DiseaseConfig:
    key: str                     # stable identifier, e.g. "diabetes"
    display_name: str            # "Diabetes"
    description: str
    feature_specs: List[FeatureSpec] = field(default_factory=list)
    model_status: str = "not_trained"  # not_trained | classical_only | classical_and_quantum

    @property
    def required_features(self) -> List[str]:
        return [spec.raw_name for spec in self.feature_specs]

    @property
    def followup_question_ids(self) -> List[str]:
        return [
            spec.question_id for spec in self.feature_specs
            if spec.source == "followup"
        ]

    def followup_questions(self):
        return followup_questions_for(self.feature_specs)


DISEASE_REGISTRY: Dict[str, DiseaseConfig] = {
    "diabetes": DiseaseConfig(
        key="diabetes",
        display_name="Diabetes",
        description=(
            "Screens for factors associated with elevated blood-glucose "
            "regulation risk."
        ),
        feature_specs=DIABETES_FEATURES,
    ),
    "heart": DiseaseConfig(
        key="heart",
        display_name="Cardiovascular disease",
        description=(
            "Screens for factors associated with elevated cardiovascular risk."
        ),
        feature_specs=HEART_FEATURES,
    ),
    "kidney": DiseaseConfig(
        key="kidney",
        display_name="Kidney disease",
        description=(
            "Screens for factors associated with elevated renal-health risk."
        ),
        feature_specs=KIDNEY_FEATURES,
    ),
}


# Reflect whatever training has actually produced on disk, rather than
# hardcoding a status that could drift out of sync with reality.
for _key, _config in DISEASE_REGISTRY.items():
    _config.model_status = model_status_for(_key)


def list_diseases() -> List[DiseaseConfig]:
    return list(DISEASE_REGISTRY.values())


def get_disease(key: str) -> Optional[DiseaseConfig]:
    return DISEASE_REGISTRY.get(key)
