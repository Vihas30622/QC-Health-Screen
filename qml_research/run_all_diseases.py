"""
run_all_diseases.py
====================
Runs the shared QML pipeline across Breast Cancer, Heart Disease, and Diabetes,
then produces per-disease plots plus a cross-disease comparison chart and JSON summary.
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_loaders import DISEASE_LOADERS
from qml_pipeline import DiseaseQMLPipeline

MODEL_COLORS = {
    "Logistic Regression": "#E8734A",
    "SVM (RBF kernel)": "#1FA774",
    "Variational Quantum Classifier": "#7B2FF7",
    "Hybrid Quantum Kernel + SVM": "#2F6FE8",
}


def plot_training_curve(history, disease_name, path):
    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(history["epoch"], history["train_loss"], color="#7B2FF7", label="Train loss (MSE)")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Loss", color="#7B2FF7")
    ax1.tick_params(axis="y", labelcolor="#7B2FF7")
    ax2 = ax1.twinx()
    ax2.plot(history["epoch"], history["train_acc"], color="#1FA774", label="Train accuracy")
    ax2.plot(history["epoch"], history["test_acc"], color="#E8734A", linestyle="--", label="Test accuracy")
    ax2.set_ylabel("Accuracy"); ax2.set_ylim(0, 1.05)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower right", fontsize=8)
    plt.title(f"VQC Training Curve — {disease_name}")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def plot_confusion_matrices(pipe, disease_name, classes, path):
    model_map = {**pipe.results["classical"],
                 "Variational Quantum Classifier": pipe.results["vqc"],
                 "Hybrid Quantum Kernel + SVM": pipe.results["hybrid_qkernel"]}
    fig, axes = plt.subplots(1, len(model_map), figsize=(4 * len(model_map), 3.5))
    for ax, (name, res) in zip(axes, model_map.items()):
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(pipe.y_test, res["y_pred"])
        ax.imshow(cm, cmap="Purples")
        ax.set_title(name, fontsize=9)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
        ax.set_xticks([0, 1]); ax.set_xticklabels(classes, fontsize=7, rotation=15)
        ax.set_yticks([0, 1]); ax.set_yticklabels(classes, fontsize=7)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.suptitle(f"Confusion Matrices — {disease_name}", y=1.03)
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_cross_disease_comparison(all_metrics, path):
    diseases = list(all_metrics.keys())
    models = ["Logistic Regression", "SVM (RBF kernel)",
              "Variational Quantum Classifier", "Hybrid Quantum Kernel + SVM"]

    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.2
    x = np.arange(len(diseases))
    for i, model in enumerate(models):
        accs = [all_metrics[d].get(model, {}).get("accuracy", 0) for d in diseases]
        ax.bar(x + (i - 1.5) * width, accs, width, label=model, color=MODEL_COLORS.get(model))
    ax.set_xticks(x); ax.set_xticklabels(diseases)
    ax.set_ylabel("Test Accuracy")
    ax.set_ylim(0, 1.0)
    ax.set_title("Model Accuracy Across Diseases")
    ax.legend(fontsize=8, loc="lower right")
    ax.axhline(0.5, color="gray", linestyle=":", linewidth=1)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def run_single_disease(key):
    """Run the pipeline for one disease and merge results into all_results.json."""
    loader = DISEASE_LOADERS[key]
    X, y, feat_names, disease_name, classes = loader()
    print(f"\n{'='*70}\nRunning pipeline for: {disease_name} (n={len(X)}, features={len(feat_names)})\n{'='*70}")

    pipe = DiseaseQMLPipeline(
        X, y, disease_name,
        n_qubits=4, n_layers=2, n_epochs=40, batch_size=15,
        learning_rate=0.25, train_subset=150,
    )
    metrics = pipe.run_all(verbose=True)

    safe_name = disease_name.lower().replace(" ", "_")
    plot_training_curve(pipe.results["vqc"]["history"], disease_name,
                         f"vqc_training_{safe_name}.png")
    plot_confusion_matrices(pipe, disease_name, classes, f"confusion_{safe_name}.png")

    print(f"\n--- {disease_name} results ---")
    for name, m in metrics.items():
        print(f"  {name:32s} acc={m['accuracy']:.3f} prec={m['precision']:.3f} "
              f"rec={m['recall']:.3f} f1={m['f1']:.3f} auc={m['roc_auc']:.3f} "
              f"time={m['train_time_s']:.2f}s")

    # merge into persistent JSON
    try:
        with open("all_results.json") as f:
            store = json.load(f)
    except FileNotFoundError:
        store = {"metrics": {}, "dataset_info": {}, "histories": {}}

    store["metrics"][disease_name] = metrics
    store["histories"][disease_name] = pipe.results["vqc"]["history"]
    store["dataset_info"][disease_name] = {
        "n_samples": len(X), "n_features_original": len(feat_names),
        "n_qubits_used": pipe.n_qubits, "pca_explained_variance": pipe.explained_var,
        "positive_rate": float(np.mean(y)),
    }
    with open("all_results.json", "w") as f:
        json.dump(store, f, indent=2)
    print(f"\nSaved results for {disease_name} to all_results.json")


def finalize():
    with open("all_results.json") as f:
        store = json.load(f)
    plot_cross_disease_comparison(store["metrics"], "cross_disease_comparison.png")
    print("Saved cross_disease_comparison.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        finalize()
    elif len(sys.argv) > 1:
        run_single_disease(sys.argv[1])
    else:
        for k in DISEASE_LOADERS:
            run_single_disease(k)
        finalize()
