"""
ml/quantum/vqc_model.py
=========================
Wraps qiskit-machine-learning's VQC (Variational Quantum Classifier) in
the same fit/predict/predict_proba shape as the classical sklearn models,
so it drops straight into `ml.common.evaluation.fit_and_evaluate` without
that function needing to know it's looking at a quantum circuit.

Uses a statevector simulator (the default backend for VQC when none is
supplied) — this is Section 15's "use a quantum simulator for
development/testing," not real quantum hardware. Real-hardware execution
via IBM Quantum Runtime is a documented optional extension, not built
here, and the app must keep working without it (Section 15).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from ml.quantum.circuit import build_ansatz, build_feature_map


class VQCDiseaseClassifier:
    """Sklearn-shaped wrapper around qiskit_machine_learning.algorithms.VQC."""

    def __init__(
        self,
        n_qubits: int,
        feature_map_reps: int = 2,
        ansatz_reps: int = 2,
        maxiter: int = 100,
        seed: int = 42,
    ):
        self.n_qubits = n_qubits
        self.feature_map_reps = feature_map_reps
        self.ansatz_reps = ansatz_reps
        self.maxiter = maxiter
        self.seed = seed
        self._vqc = None

    def _build(self):
        # Imported lazily so the rest of the ml/ package works even in
        # environments without qiskit installed (only quantum training
        # requires it).
        from qiskit_machine_learning.algorithms import VQC
        from qiskit_machine_learning.optimizers import COBYLA
        from qiskit_machine_learning.utils import algorithm_globals

        algorithm_globals.random_seed = self.seed

        feature_map = build_feature_map(self.n_qubits, reps=self.feature_map_reps)
        ansatz = build_ansatz(self.n_qubits, reps=self.ansatz_reps)

        return VQC(
            feature_map=feature_map,
            ansatz=ansatz,
            optimizer=COBYLA(maxiter=self.maxiter),
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "VQCDiseaseClassifier":
        self._vqc = self._build()
        self._vqc.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._vqc is None:
            raise RuntimeError("Call fit() before predict().")
        return self._vqc.predict(X)

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        # Not every VQC configuration exposes calibrated probabilities —
        # when it doesn't, evaluation.py's hasattr/try-except handles the
        # absence by leaving roc_auc as None rather than a fabricated
        # number.
        if self._vqc is None:
            raise RuntimeError("Call fit() before predict_proba().")
        if not hasattr(self._vqc, "predict_proba"):
            raise AttributeError("Underlying VQC does not expose predict_proba.")
        return self._vqc.predict_proba(X)

    @property
    def n_circuit_layers(self) -> int:
        return self.feature_map_reps + self.ansatz_reps
