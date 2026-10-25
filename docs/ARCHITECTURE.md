# Architecture & Documentation

This expands on the top-level README with the fuller narrative the
original spec's documentation section asked for. Where something isn't
built yet, that's stated plainly rather than glossed over.

## 1–3. Motivation, problem statement, objectives

Health-risk screening tools are usually single-disease (a diabetes
calculator, a heart-risk calculator) and ask the user to already know
which condition to check. The objective here was a system that starts
from general health information, narrows toward specific conditions
through targeted follow-up, and compares a classical ML baseline against
a genuine quantum ML classifier for each condition — without claiming
either approach is inherently better, and without ever presenting a
probability as a diagnosis.

## 4. System architecture

```
Frontend (React/Vite)  <-->  Backend API (FastAPI)  <-->  ML/QML Engine (scikit-learn + Qiskit)
                                     |
                              Session store (in-memory, TTL'd, no DB)
                                     |
                         Model Storage (models/<disease>/*.joblib + metrics.json)
                                     |
                         Dataset/Training Pipeline (ml/training/train_disease.py)
```

The backend never trains a model on a request — it only loads what
`ml/training/train_disease.py` already saved to disk. Training and
inference are fully separate processes, run at different times.

## 5. User workflow

Landing → Basic Health Profile → Initial Screening (coarse, profile-only)
→ pick a flagged condition → targeted follow-up questions → prediction
(full lab-feature model) → repeat for other conditions or skip → final
report → optional model-comparison / quantum-circuit views.

## 6. Dataset descriptions

| Disease | Source | Samples | Features | License |
|---|---|---|---|---|
| Diabetes | Pima Indians Diabetes dataset | 768 | 8 | Public domain / commonly redistributed |
| Heart disease | UCI Heart Disease (Cleveland subset) | 303 | 13 | UCI ML Repository |
| Kidney disease | UCI Chronic Kidney Disease (Rubini, Soundarapandian & Eswaran, 2015) | 158 (complete-case subset of 400) | 24 | CC BY 4.0 |

The kidney dataset was sourced during Phase 9 via
`https://lisds.github.io/textbook/data/chronic_kidney_disease.html`, a
processed, complete-case redistribution of the original UCI dataset.

**A finding worth stating plainly:** all three classical models score
**100% accuracy** on the kidney test split. This was checked for a data
leak (none found — proper stratified split, preprocessing fit on the
training data only) and is a documented characteristic of this
particular dataset: it's small (158 rows), the two classes are strongly
separated by a few lab values (specific gravity, albumin, hemoglobin,
serum creatinine), and the test split is only 40 rows. Treat this
number as "this dataset is easy," not "kidney disease is easy to
predict" — it would very likely not replicate on a larger, noisier,
real-world clinical population.

## 7. Data preprocessing

Each dataset gets its own `DiseasePreprocessor` (`ml/common/preprocessor.py`):
sentinel-zero values in physiologically-impossible columns (the Pima
dataset's recorded `0` for glucose/BMI/etc.) are treated as missing and
median-imputed — fit on the training split only — then all features are
standard-scaled. This preprocessor is pickled alongside the model and
reused unchanged at inference time.

## 8. Classical ML algorithms

Logistic Regression, SVM (RBF kernel), and Random Forest
(`ml/classical/models.py`), each evaluated with the same metric set
(`ml/common/evaluation.py`). The best-performing model by test-set F1 is
what `/api/prediction/{disease}` actually uses (`best_classical_model_name`
in `backend/services/model_loader.py`) — chosen mechanically from a
number already computed at training time, not hand-picked.

## 9. Quantum ML algorithm

A Variational Quantum Classifier (`ml/quantum/vqc_model.py`) built on
Qiskit + Qiskit Machine Learning: PCA reduces each disease's features to
4 qubits, values are scaled to `[0, π]`, a ZZ feature map encodes them,
and a trainable RY/RZ + CZ ansatz follows. The quantum libraries are
available in the current development environment; circuit rendering
and a small VQC fit/predict smoke test have been exercised. The
checked-in model metrics do not contain trained quantum-model results,
however; the full disease training pipeline remains unverified.
Training is optional and may take a while on the local statevector
simulator.

## 10. Quantum feature encoding

Angle encoding via rotation gates: each of the 4 PCA components becomes
a qubit rotation angle in `[0, π]`. See
`ml/quantum/dimensionality_reduction.py` — this part **was** verified
directly in this environment (it only needs scikit-learn), including
correct handling of datasets with fewer raw features than the requested
qubit count.

## 11. Quantum circuit architecture

ZZ feature map (2 repetitions, linear entanglement) → RY/RZ rotation +
CZ entangler ansatz (2 repetitions) → measurement. See
`ml/quantum/circuit.py`; `circuit_text_diagram()` renders the actual
circuit as ASCII art, exposed via `GET /api/circuit/{disease}` and shown in
the frontend's "How it works" page (falls back to an honest message
when qiskit isn't installed, rather than a placeholder image). Circuit
rendering was verified in the current environment.

## 12. Training process

`ml/training/train_disease.py`, run standalone per disease or via
`all`: load → clean/impute → stratified 75/25 split → scale → train
three classical models + (if qiskit is present) one VQC on a capped
sample subset + a separate lighter "initial screening" model on
profile-only features → evaluate all of them → save every model,
preprocessor, and the full metrics to `models/<disease>/`.

## 13. Evaluation metrics

Accuracy, precision, recall, F1, ROC-AUC (where the model supports
`predict_proba`), confusion matrix, training time, inference time,
feature count — computed for every classical model on every disease,
and additionally qubit count, circuit layers, and simulator identity for
the quantum model. Nothing here is a placeholder; every number comes
from an actual `fit`/`predict` call in `ml/common/evaluation.py`. The
same real predictions also drive `ml/common/charts.py`, which writes an
actual confusion-matrix PNG and (where `predict_proba` exists) an ROC
curve per model, plus one grouped-bar model-comparison chart per
disease, to `models/<disease>/charts/`. These are served through
`GET /api/models/{disease}/charts/{filename}`, which checks the filename
against an explicit allowlist so it can never be used to fetch the raw
`.joblib` model files (Section 16's "never expose internal model
files").

## 14. Classical vs quantum comparison

Exposed via `GET /api/models` (real, per-disease JSON with chart image
URLs) and the frontend's Model Comparison page, which renders the
actual confusion-matrix/ROC-curve images inline per model plus the
grouped-bar comparison chart. The checked-in metrics currently contain
no quantum results (see §9), so only the classical models are compared
until the VQC training run is completed.

## 15–18. Installation, running the backend/frontend, training models, running predictions

See the top-level README's "Run locally" and "Train the models"
sections. The FastAPI tests and local API flow have been exercised, as
has the frontend production build. The Docker image build could not run
because the Docker Linux engine was unavailable in the current
environment.

## 19. Future scope

- Run VQC training end to end and address any runtime issues it surfaces.
- Replace or supplement the heart-disease dataset — most of its
  features require ECG/stress-test/fluoroscopy results a self-screening
  user won't have, so `/api/prediction/heart` will legitimately return
  "insufficient information" most of the time. The Framingham Heart
  Study dataset (~4,240 records, questionnaire/basic-lab features →
  10-year CHD risk) is a concrete, better-suited candidate — attempted
  in this session but not completed, since the available raw-CSV
  sources returned with row-delimiting newlines stripped by this
  environment's fetch tooling, and reconstructing ~4,240 rows from a
  flattened numeric blob by hand risks silently corrupting the data.
  Worth a normal `wget`/browser download instead.
- A larger, less separable kidney dataset, to get a more realistic
  accuracy signal than the current 100%.
- Persistent, opt-in storage for returning users (currently fully
  session-based and ephemeral by design).
- Real IBM Quantum hardware execution as an optional path (Section 15
  of the original spec explicitly keeps this optional).

## 20. Limitations

- Two of three diseases (heart, and several diabetes fields) need lab
  or diagnostic-test values most users won't have on hand — a real
  limitation of building on these specific academic datasets for a
  self-screening tool, not a bug in the follow-up flow.
- The kidney dataset's 100% test accuracy (see §6) should not be read
  as "kidney disease is easy to predict."
- Quantum circuit rendering and encoding are verified, but no trained
  VQC results are present in the checked-in model metrics; the complete
  VQC training run remains unverified (see §9).
- No real-world clinical validation has been done on any of these
  models; they're research/demonstration datasets.
- The Docker image build was not verified because the Docker Linux
  engine/daemon was not running.

## 21. Testing

`backend/tests/` (pytest + FastAPI TestClient) covers input validation,
session isolation, the screening→follow-up→prediction→report flow,
model loading, and chart/circuit endpoints. `ml/tests/` covers dataset
loaders, preprocessing, quantum encoding, charts, and evaluation. All
58 backend and ML tests pass in the current environment. A separate API
smoke flow also completed QR import, initial screening, follow-up and
prediction for all three diseases, report generation, model metrics and
chart retrieval, and circuit rendering.

## 22. Medical disclaimer

This system provides experimental health-risk estimates using machine
learning and quantum machine learning. It is not a medical diagnosis
and should not replace professional medical advice.
