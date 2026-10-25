"""
ml/common/charts.py
=====================
Section 12 of the spec asks for confusion matrix, ROC curve, and
accuracy/precision/recall/F1 comparison charts. Every chart here is
plotted from actual arrays produced during training/evaluation — nothing
is drawn from typed-in numbers.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # headless — no display available during training
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay


def plot_confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray, class_names: List[str], title: str, out_path: str
) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, display_labels=class_names, ax=ax, colorbar=False, cmap="Blues"
    )
    ax.set_title(title, fontsize=9, wrap=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_roc_curve(y_true: np.ndarray, y_proba: np.ndarray, title: str, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    RocCurveDisplay.from_predictions(y_true, y_proba, ax=ax)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    ax.set_title(title, fontsize=9, wrap=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_model_comparison(model_results: Dict[str, dict], title: str, out_path: str) -> None:
    """Grouped bar chart of accuracy/precision/recall/F1 across every
    model evaluated for one disease — the classical-vs-classical-vs-quantum
    comparison Section 12 asks for."""
    metrics = ["accuracy", "precision", "recall", "f1"]
    model_names = list(model_results.keys())

    fig, ax = plt.subplots(figsize=(max(5, len(model_names) * 1.8), 4))
    x = np.arange(len(metrics))
    width = 0.8 / max(len(model_names), 1)

    for i, name in enumerate(model_names):
        values = [model_results[name].get(m, 0) or 0 for m in metrics]
        ax.bar(x + i * width, values, width, label=name.replace("_", " "))

    ax.set_xticks(x + width * (len(model_names) - 1) / 2)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.05)
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def generate_disease_charts(
    disease_key: str,
    display_name: str,
    class_names: List[str],
    charts_dir: str,
    per_model_predictions: Dict[str, dict],
    all_model_results: Dict[str, dict],
) -> List[str]:
    """
    per_model_predictions: {model_name: {"y_true": ndarray, "y_pred": ndarray, "y_proba": Optional[ndarray]}}
    all_model_results: the same dict passed to plot_model_comparison (metrics.json's classical_models,
                        optionally with a quantum entry merged in by the caller)
    Returns the list of file paths written.
    """
    os.makedirs(charts_dir, exist_ok=True)
    written = []

    for model_name, preds in per_model_predictions.items():
        cm_path = os.path.join(charts_dir, f"confusion_{model_name}.png")
        plot_confusion_matrix(
            preds["y_true"], preds["y_pred"], class_names,
            f"{display_name} — {model_name} confusion matrix", cm_path,
        )
        written.append(cm_path)

        if preds.get("y_proba") is not None:
            roc_path = os.path.join(charts_dir, f"roc_{model_name}.png")
            plot_roc_curve(
                preds["y_true"], preds["y_proba"],
                f"{display_name} — {model_name} ROC curve", roc_path,
            )
            written.append(roc_path)

    comparison_path = os.path.join(charts_dir, "model_comparison.png")
    plot_model_comparison(all_model_results, f"{display_name} — model comparison", comparison_path)
    written.append(comparison_path)

    return written
