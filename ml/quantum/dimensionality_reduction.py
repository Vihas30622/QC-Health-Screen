"""
ml/quantum/dimensionality_reduction.py
========================================
Section 8 of the spec requires "Feature Selection / PCA" before quantum
encoding and is explicit that a manageable qubit count matters more than
a large one: simulating an n-qubit circuit costs O(2^n) classically, and
more qubits does not, by itself, improve accuracy. Every disease dataset
here (8-13 raw features) gets reduced to a small, fixed number of
qubits via PCA fit on the training split only.

A second scaling stage maps the PCA output into a bounded angle range
for rotation-gate encoding — PCA components aren't naturally bounded,
and feeding an unbounded value into an RY/RZ rotation makes the encoding
behave unpredictably (angles wrap around 2*pi).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

DEFAULT_N_QUBITS = 4


@dataclass
class QuantumEncodingPipeline:
    n_qubits: int = DEFAULT_N_QUBITS
    random_state: int = 42
    _pca: PCA = field(default=None, repr=False)
    _angle_scaler: MinMaxScaler = field(default=None, repr=False)

    def fit(self, X_train: np.ndarray) -> "QuantumEncodingPipeline":
        n_components = min(self.n_qubits, X_train.shape[1])
        self._pca = PCA(n_components=n_components, random_state=self.random_state)
        reduced = self._pca.fit_transform(X_train)

        # Angle-encode into [0, pi] rather than [0, 2*pi]: keeps rotations
        # within a single "cycle" per qubit, which is the more common
        # convention for RY/RZ feature encoding.
        self._angle_scaler = MinMaxScaler(feature_range=(0, np.pi))
        self._angle_scaler.fit(reduced)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self._pca is None or self._angle_scaler is None:
            raise RuntimeError("QuantumEncodingPipeline.fit() must be called before transform().")
        reduced = self._pca.transform(X)
        return self._angle_scaler.transform(reduced)

    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        self.fit(X_train)
        return self.transform(X_train)

    @property
    def explained_variance_ratio(self) -> list:
        if self._pca is None:
            raise RuntimeError("Call fit() first.")
        return self._pca.explained_variance_ratio_.tolist()

    @property
    def n_components(self) -> int:
        if self._pca is None:
            raise RuntimeError("Call fit() first.")
        return self._pca.n_components_
