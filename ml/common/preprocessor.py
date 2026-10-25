"""
ml/common/preprocessor.py
===========================
Common preprocessing abstraction (Section 9/10 of the spec):
  1. Missing-value handling (median imputation, fit on train only)
  2. Feature scaling (StandardScaler, fit on train only)

Kept as a single fit/transform object so it can be pickled alongside the
trained model and reused unchanged at inference time — the whole point
of separating training from prediction (Section 9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


@dataclass
class DiseasePreprocessor:
    feature_names: List[str]
    missing_value_columns: List[str] = field(default_factory=list)
    _imputer: SimpleImputer = field(default=None, repr=False)
    _scaler: StandardScaler = field(default=None, repr=False)
    _missing_col_idx: List[int] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._missing_col_idx = [
            self.feature_names.index(c)
            for c in self.missing_value_columns
            if c in self.feature_names
        ]

    def _mark_sentinel_as_nan(self, X: np.ndarray) -> np.ndarray:
        X = X.copy()
        for idx in self._missing_col_idx:
            X[X[:, idx] == 0, idx] = np.nan
        return X

    def fit(self, X_train: np.ndarray) -> "DiseasePreprocessor":
        X_marked = self._mark_sentinel_as_nan(X_train)

        self._imputer = SimpleImputer(strategy="median")
        X_imputed = self._imputer.fit_transform(X_marked)

        self._scaler = StandardScaler()
        self._scaler.fit(X_imputed)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self._imputer is None or self._scaler is None:
            raise RuntimeError("DiseasePreprocessor.fit() must be called before transform().")
        X_marked = self._mark_sentinel_as_nan(X)
        X_imputed = self._imputer.transform(X_marked)
        return self._scaler.transform(X_imputed)

    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        self.fit(X_train)
        return self.transform(X_train)
