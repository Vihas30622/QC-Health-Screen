"""
services/vitals.py
====================
Small, pure, testable helpers for derived vitals. Kept separate from the
schema layer so they can be reused by the (future) preprocessing pipeline
without importing pydantic models.
"""

from __future__ import annotations


def compute_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def categorize_bmi(bmi: float) -> str:
    # Standard WHO adult BMI categories. This is a screening label, not a
    # diagnosis, and does not account for age/sex/ethnicity-specific
    # nuance — that caveat is surfaced to the user in the UI copy.
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "healthy_range"
    if bmi < 30:
        return "overweight"
    return "obesity_range"
