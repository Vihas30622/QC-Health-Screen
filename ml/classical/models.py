"""
ml/classical/models.py
========================
The classical baseline models (Section 7 of the spec). Kept as a factory
function, not module-level instances, so each disease gets freshly
initialized (unfitted) models rather than accidentally sharing state.
"""

from __future__ import annotations

from typing import Dict

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

RANDOM_STATE = 42


def build_classical_models() -> Dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE
        ),
        "svm": SVC(kernel="rbf", probability=True, random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=6, random_state=RANDOM_STATE
        ),
    }
