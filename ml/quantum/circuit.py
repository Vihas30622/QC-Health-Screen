"""
ml/quantum/circuit.py
=======================
Builds the feature map + ansatz pair that VQC assembles into a full
variational quantum circuit (Section 8 of the spec):

    Quantum Feature Encoding -> Quantum Feature Map -> Variational Circuit

A ZZ feature map encodes each classical feature as a qubit rotation, with
entangling ZZ interactions between qubits so the map isn't just a product
of independent single-qubit rotations. `n_local` builds the trainable
ansatz that follows it — alternating RY/RZ rotation layers with CZ
entanglers, matching the RY + entangler pattern shown in the spec's own
circuit diagram (Section 19).

Kept deliberately small (a handful of qubits, 2 reps): Section 8 is
explicit that more qubits or layers isn't claimed to help — the qubit
count here is set by PCA in `dimensionality_reduction.py`, not by a
belief that more is better.
"""

from __future__ import annotations

from qiskit.circuit.library import n_local, zz_feature_map


def build_feature_map(n_qubits: int, reps: int = 2):
    """ZZ feature map: encodes each of the n_qubits (post-PCA) features as
    a qubit rotation, with ZZ entanglement between qubits carrying
    pairwise feature interactions into the encoding itself."""
    return zz_feature_map(feature_dimension=n_qubits, reps=reps, entanglement="linear")


def build_ansatz(n_qubits: int, reps: int = 2):
    """Trainable variational layer: RY/RZ single-qubit rotations with CZ
    entanglers between adjacent qubits, repeated `reps` times."""
    return n_local(n_qubits, ["ry", "rz"], "cz", entanglement="linear", reps=reps)


def circuit_text_diagram(n_qubits: int, feature_map_reps: int = 2, ansatz_reps: int = 2) -> str:
    """Renders the full encoding + ansatz circuit as ASCII art — used by
    the (future) 'How it works' quantum-visualization page so the UI shows
    the actual circuit being run, not a generic illustration."""
    feature_map = build_feature_map(n_qubits, reps=feature_map_reps)
    ansatz = build_ansatz(n_qubits, reps=ansatz_reps)
    full_circuit = feature_map.compose(ansatz)
    return str(full_circuit.decompose().draw(output="text"))
