"""
backend/core/feature_spec.py
==============================
One FeatureSpec per raw model feature, in the exact order the trained
model/preprocessor expects. This single list drives three things so they
can never drift out of sync with each other:

  1. Which follow-up questions get asked (Phase 8) — anything with
     source="followup".
  2. How a basic profile + follow-up answers get turned into the raw
     feature vector a trained model can score (Phase 6).
  3. The human-readable factor labels used in the explainability section
     (Phase 14).

Section 6 of the spec is explicit: if a value isn't reasonably obtainable
and the user hasn't supplied it, the prediction must be marked
"insufficient information" — never silently filled in. That's exactly
what `resolve_feature_vector` does: any missing required feature aborts
the whole vector rather than defaulting it to 0 or a population average.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class FeatureSpec:
    raw_name: str          # must match the trained model's feature_names exactly, in order
    label: str              # human-readable label for questions/explanations
    source: str              # "profile" | "followup"
    question_type: str = "number"  # number | boolean | select
    unit: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None  # [{"value": "...", "label": "..."}]
    question_id: Optional[str] = None   # required if source == "followup"
    help_text: Optional[str] = None
    extractor: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Optional[float]]] = None
    # extractor(profile_dict, followup_answers_dict) -> float | None
    # If omitted, defaults to looking up question_id in followup_answers.


def _default_extractor(spec: FeatureSpec):
    def _extract(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
        val = followup.get(spec.question_id)
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
    return _extract


def resolve_feature_vector(
    specs: List[FeatureSpec],
    profile: Dict[str, Any],
    followup_answers: Dict[str, Any],
) -> Tuple[Optional[List[float]], List[str]]:
    """Returns (vector, missing_labels). vector is None if anything required
    is missing — the caller is expected to report 'insufficient information'
    in that case rather than guessing."""
    values: List[float] = []
    missing: List[str] = []

    for spec in specs:
        extractor = spec.extractor or _default_extractor(spec)
        val = extractor(profile, followup_answers)
        if val is None:
            missing.append(spec.label)
        else:
            values.append(float(val))

    if missing:
        return None, missing
    return values, []


def followup_questions_for(specs: List[FeatureSpec]) -> List[Dict[str, Any]]:
    """Question definitions for the Step 4 targeted follow-up UI —
    anything sourced from the user rather than the basic profile."""
    questions = []
    for spec in specs:
        if spec.source != "followup":
            continue
        questions.append({
            "id": spec.question_id,
            "label": spec.label,
            "type": spec.question_type,
            "unit": spec.unit,
            "options": spec.options,
            "help_text": spec.help_text,
        })
    return questions
