"""
qml_pipeline.py
===============
Generalized pipeline shared across all diseases:
  1. Preprocess (scale -> PCA to n_qubits -> angle-encode to [0, pi])
  2. Classical baselines: Logistic Regression, SVM (RBF)
  3. Quantum: Variational Quantum Classifier (VQC), trained end-to-end with quantum gradients
  4. Hybrid: Quantum Kernel method - quantum feature map produces a kernel matrix
     (via simulated statevector overlaps), fed into a classical SVM
"""

import time
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, roc_auc_score)

RNG_SEED = 42
np.random.seed(RNG_SEED)


class DiseaseQMLPipeline:
    def __init__(self, X, y, disease_name, n_qubits=4, n_layers=2,
                 n_epochs=40, batch_size=15, learning_rate=0.25, train_subset=150):
        self.X, self.y = X, y
        self.disease_name = disease_name
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.train_subset = train_subset

        self.dev = qml.device("default.qubit", wires=n_qubits)
        self._build_circuits()
        self.results = {}

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------
    def preprocess(self):
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.25, random_state=RNG_SEED, stratify=self.y
        )
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        n_components = min(self.n_qubits, X_train_s.shape[1])
        pca = PCA(n_components=n_components, random_state=RNG_SEED)
        X_train_p = pca.fit_transform(X_train_s)
        X_test_p = pca.transform(X_test_s)
        self.explained_var = float(pca.explained_variance_ratio_.sum())

        angle_scaler = MinMaxScaler(feature_range=(0, np.pi))
        X_train_a = angle_scaler.fit_transform(X_train_p)
        X_test_a = np.clip(angle_scaler.transform(X_test_p), 0, np.pi)

        self.X_train_full, self.X_test_full = X_train_s, X_test_s  # full-feature classical reference
        self.X_train_a, self.X_test_a = X_train_a, X_test_a         # PCA + angle-encoded
        self.y_train, self.y_test = y_train, y_test
        return self

    # ------------------------------------------------------------------
    # Quantum circuits
    # ------------------------------------------------------------------
    def _build_circuits(self):
        n_qubits, n_layers = self.n_qubits, self.n_layers

        def feature_map(x):
            for i in range(n_qubits):
                qml.RY(x[i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        def ansatz(weights):
            for layer in range(n_layers):
                for i in range(n_qubits):
                    qml.RY(weights[layer, i, 0], wires=i)
                    qml.RZ(weights[layer, i, 1], wires=i)
                for i in range(n_qubits):
                    qml.CNOT(wires=[i, (i + 1) % n_qubits])

        @qml.qnode(self.dev)
        def vqc_circuit(weights, x):
            feature_map(x)
            ansatz(weights)
            return qml.expval(qml.PauliZ(0))

        @qml.qnode(self.dev)
        def state_circuit(x):
            feature_map(x)
            return qml.state()

        self._feature_map = feature_map
        self.vqc_circuit = vqc_circuit
        self.state_circuit = state_circuit

    # ------------------------------------------------------------------
    # Classical baselines
    # ------------------------------------------------------------------
    def run_classical(self):
        out = {}
        for name, model in [
            ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=RNG_SEED)),
            ("SVM (RBF kernel)", SVC(kernel="rbf", probability=True, random_state=RNG_SEED)),
        ]:
            t0 = time.time()
            model.fit(self.X_train_a, self.y_train)
            elapsed = time.time() - t0
            y_pred = model.predict(self.X_test_a)
            y_score = model.predict_proba(self.X_test_a)[:, 1]
            out[name] = {"y_pred": y_pred, "y_score": y_score, "train_time_s": elapsed}
        self.results["classical"] = out
        return out

    # ------------------------------------------------------------------
    # Quantum: Variational Quantum Classifier
    # ------------------------------------------------------------------
    def run_vqc(self, verbose=True):
        y_train_pm1 = np.where(self.y_train == 1, 1, -1).astype(float)
        y_test_pm1 = np.where(self.y_test == 1, 1, -1).astype(float)

        n = len(self.X_train_a)
        if n > self.train_subset:
            idx = np.random.choice(n, self.train_subset, replace=False)
            X_sub, y_sub = self.X_train_a[idx], y_train_pm1[idx]
        else:
            X_sub, y_sub = self.X_train_a, y_train_pm1

        weights = pnp.array(0.1 * np.random.randn(self.n_layers, self.n_qubits, 2), requires_grad=True)
        bias = pnp.array(0.0, requires_grad=True)
        opt = qml.NesterovMomentumOptimizer(stepsize=self.learning_rate)

        def cost(weights, bias, X_batch, y_batch):
            preds = pnp.stack([self.vqc_circuit(weights, x) for x in X_batch]) + bias
            return pnp.mean((pnp.array(y_batch) - preds) ** 2)

        history = {"epoch": [], "train_loss": [], "train_acc": [], "test_acc": []}
        t0 = time.time()
        n_sub = len(X_sub)
        for epoch in range(self.n_epochs):
            perm = np.random.permutation(n_sub)
            for start in range(0, n_sub, self.batch_size):
                b = perm[start:start + self.batch_size]
                weights, bias, _, _ = opt.step(cost, weights, bias, X_sub[b], y_sub[b])

            train_preds = np.array([self.vqc_circuit(weights, x) for x in X_sub]) + float(bias)
            test_preds = np.array([self.vqc_circuit(weights, x) for x in self.X_test_a]) + float(bias)
            train_loss = float(np.mean((y_sub - train_preds) ** 2))
            train_acc = float(np.mean(np.sign(train_preds) == y_sub))
            test_acc = float(np.mean(np.sign(test_preds) == y_test_pm1))

            history["epoch"].append(epoch + 1)
            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["test_acc"].append(test_acc)

            if verbose and ((epoch + 1) % 10 == 0 or epoch == 0):
                print(f"  [{self.disease_name} VQC] epoch {epoch+1:3d}/{self.n_epochs} | "
                      f"loss={train_loss:.4f} | train_acc={train_acc:.3f} | test_acc={test_acc:.3f}")

        elapsed = time.time() - t0
        final_test_preds = np.array([self.vqc_circuit(weights, x) for x in self.X_test_a]) + float(bias)
        y_pred = np.where(np.sign(final_test_preds) >= 0, 1, 0)
        y_score = (final_test_preds + 1) / 2

        self.results["vqc"] = {
            "y_pred": y_pred, "y_score": y_score, "train_time_s": elapsed,
            "history": history, "weights": weights, "bias": float(bias), "n_train_used": n_sub,
        }
        return self.results["vqc"]

    # ------------------------------------------------------------------
    # Hybrid: Quantum Kernel + classical SVM
    # ------------------------------------------------------------------
    def run_quantum_kernel_hybrid(self):
        n_train_cap = min(len(self.X_train_a), self.train_subset)
        idx = np.random.choice(len(self.X_train_a), n_train_cap, replace=False)
        X_train_k, y_train_k = self.X_train_a[idx], self.y_train[idx]

        t0 = time.time()
        train_states = np.array([self.state_circuit(x) for x in X_train_k])
        test_states = np.array([self.state_circuit(x) for x in self.X_test_a])

        K_train = np.abs(train_states @ train_states.conj().T) ** 2
        K_test = np.abs(test_states @ train_states.conj().T) ** 2

        svm = SVC(kernel="precomputed", probability=True, random_state=RNG_SEED)
        svm.fit(K_train.real, y_train_k)
        elapsed = time.time() - t0

        y_pred = svm.predict(K_test.real)
        y_score = svm.predict_proba(K_test.real)[:, 1]

        self.results["hybrid_qkernel"] = {
            "y_pred": y_pred, "y_score": y_score, "train_time_s": elapsed, "n_train_used": n_train_cap,
        }
        return self.results["hybrid_qkernel"]

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def compute_all_metrics(self):
        metrics = {}
        model_map = {}
        for name, res in self.results.get("classical", {}).items():
            model_map[name] = res
        if "vqc" in self.results:
            model_map["Variational Quantum Classifier"] = self.results["vqc"]
        if "hybrid_qkernel" in self.results:
            model_map["Hybrid Quantum Kernel + SVM"] = self.results["hybrid_qkernel"]

        for name, res in model_map.items():
            metrics[name] = {
                "accuracy": accuracy_score(self.y_test, res["y_pred"]),
                "precision": precision_score(self.y_test, res["y_pred"], zero_division=0),
                "recall": recall_score(self.y_test, res["y_pred"], zero_division=0),
                "f1": f1_score(self.y_test, res["y_pred"], zero_division=0),
                "roc_auc": roc_auc_score(self.y_test, res["y_score"]),
                "confusion_matrix": confusion_matrix(self.y_test, res["y_pred"]).tolist(),
                "train_time_s": res["train_time_s"],
            }
        self.metrics = metrics
        return metrics

    def run_all(self, verbose=True):
        self.preprocess()
        self.run_classical()
        self.run_vqc(verbose=verbose)
        self.run_quantum_kernel_hybrid()
        return self.compute_all_metrics()
