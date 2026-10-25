# Quantum Machine Learning for Multi-Disease Prediction

A scalable hybrid quantum-classical framework that predicts three diseases
(Heart Disease, Diabetes, Breast Cancer) using a shared preprocessing and
quantum-encoding pipeline, comparing classical, quantum, and hybrid models.

## Project structure

```
data_loaders.py          Loads and standardizes each disease dataset into a common interface
qml_pipeline.py           Core reusable pipeline: preprocessing, classical baselines,
                          Variational Quantum Classifier (VQC), and the quantum-kernel
                          hybrid model, plus metrics computation
run_all_diseases.py       Driver script: runs the pipeline per disease, saves plots
                          and a merged all_results.json
make_architecture_diagram.py   Generates the architecture diagram (matplotlib)
build_report.js           Generates the Word report (docx) from all_results.json + plots
data/                     heart.csv (UCI Heart Disease), diabetes.csv (Pima Indians)
                          (Breast Cancer loads directly from sklearn, no file needed)
all_results.json          All numeric results (metrics + training history) for every
                          disease and model
*.png                     Generated plots (training curves, confusion matrices,
                          cross-disease comparison, architecture diagram)
QML_Multi_Disease_Prediction_Report.docx   Full technical report
```

## Requirements

```bash
pip install pennylane scikit-learn numpy pandas matplotlib --break-system-packages
```

## Running

Run everything (all three diseases, ~8-10 minutes total since each VQC trains
for 40 epochs on a simulated quantum circuit):

```bash
python3 run_all_diseases.py
```

Or run a single disease (faster, useful for testing/iterating):

```bash
python3 run_all_diseases.py heart_disease     # ~2.5 min
python3 run_all_diseases.py diabetes          # ~3 min
python3 run_all_diseases.py breast_cancer     # ~3 min
python3 run_all_diseases.py finalize          # regenerate cross-disease comparison chart only
```

Valid disease keys: `heart_disease`, `diabetes`, `breast_cancer`.

## Extending to a new disease

1. Add a loader function to `data_loaders.py` following the existing pattern:
   return `(X, y, feature_names, disease_name, class_names)` where `y` is
   binary (1 = disease present).
2. Register it in the `DISEASE_LOADERS` dict.
3. Run `python3 run_all_diseases.py <your_new_key>`.

No changes to `qml_pipeline.py` are needed — that's the point of the shared
framework design.

## Key methodology notes

- All quantum circuits run on PennyLane's `default.qubit` simulator (exact
  statevector, no hardware noise) — see the report's Limitations section.
- Features are PCA-reduced to 4 components (= 4 qubits) before quantum
  encoding, since simulating more qubits gets expensive quickly.
- The VQC trains end-to-end via quantum gradients (parameter-shift rule).
  The "Hybrid" model instead uses a fixed quantum feature map to build a
  kernel matrix (via simulated statevector overlaps) for a classical SVM —
  much faster to train, no quantum parameter optimization needed.

See the accompanying Word report for full methodology, results, discussion,
limitations, and future scope.
