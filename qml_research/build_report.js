const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, AlignmentType, TableOfContents,
  PageBreak, LevelFormat, convertInchesToTwip, PositionalTab, PositionalTabAlignment,
  PositionalTabLeader, PositionalTabRelativeTo,
} = require("docx");

function tocLine(title, pageNum) {
  return new Paragraph({
    children: [
      new TextRun({ text: title }),
      new TextRun({
        children: [new PositionalTab({
          alignment: PositionalTabAlignment.RIGHT,
          leader: PositionalTabLeader.DOT,
          relativeTo: PositionalTabRelativeTo.MARGIN,
        })],
      }),
      new TextRun({ text: String(pageNum) }),
    ],
    spacing: { after: 120 },
  });
}
const fs = require("fs");

const PURPLE = "5E35B1";
const DARK = "222222";
const GREY = "666666";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 160 },
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
  });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20, color: GREY })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  });
}
function image(path, widthPx, heightPx) {
  return new Paragraph({
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: widthPx, height: heightPx } })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
  });
}

function cell(text, { header = false, width = 1000, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: "EDE7F6" } : undefined,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: header, size: header ? 20 : 20 })],
      alignment: align,
    })],
  });
}

function makeTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((hText, i) => cell(hText, { header: true, width: widths[i] })) }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(String(c), { width: widths[i] })) })),
    ],
  });
}

// ---------------------------------------------------------------------
// Load numeric results
// ---------------------------------------------------------------------
const results = JSON.parse(fs.readFileSync("all_results.json", "utf-8"));
const diseases = ["Breast Cancer", "Heart Disease", "Diabetes"];
const models = ["Logistic Regression", "SVM (RBF kernel)", "Variational Quantum Classifier", "Hybrid Quantum Kernel + SVM"];

function metricRow(disease) {
  return models.map(m => {
    const met = results.metrics[disease][m];
    return [m, met.accuracy.toFixed(3), met.precision.toFixed(3), met.recall.toFixed(3), met.f1.toFixed(3), met.roc_auc.toFixed(3)];
  });
}

const datasetRows = diseases.map(d => {
  const info = results.dataset_info[d];
  return [d, info.n_samples, info.n_features_original, info.n_qubits_used,
          (info.pca_explained_variance * 100).toFixed(1) + "%", (info.positive_rate * 100).toFixed(1) + "%"];
});

// ---------------------------------------------------------------------
// Build document
// ---------------------------------------------------------------------
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22, color: DARK } } },
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: [
      // Title page
      new Paragraph({ text: "", spacing: { before: 1200 } }),
      new Paragraph({
        children: [new TextRun({ text: "A Scalable Hybrid Quantum-Classical Framework", bold: true, size: 40, color: PURPLE })],
        alignment: AlignmentType.CENTER, spacing: { after: 120 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "for Multi-Disease Prediction", bold: true, size: 40, color: PURPLE })],
        alignment: AlignmentType.CENTER, spacing: { after: 400 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Quantum Machine Learning applied to Heart Disease, Diabetes, and Breast Cancer diagnosis", size: 24, italics: true, color: GREY })],
        alignment: AlignmentType.CENTER, spacing: { after: 800 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Technical Project Report", size: 24 })],
        alignment: AlignmentType.CENTER, spacing: { after: 100 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "September 2026", size: 22, color: GREY })],
        alignment: AlignmentType.CENTER,
      }),
      new Paragraph({ children: [new PageBreak()] }),

      // TOC (manual, since field-based TOC requires opening in Word to populate)
      h1("Table of Contents"),
      tocLine("Abstract", 3),
      tocLine("1. Introduction", 3),
      tocLine("2. Background", 4),
      tocLine("3. Related Work", 5),
      tocLine("4. Datasets", 5),
      tocLine("5. System Architecture", 6),
      tocLine("6. Methodology", 6),
      tocLine("7. Results", 7),
      tocLine("   7.1 Breast Cancer", 8),
      tocLine("   7.2 Heart Disease", 8),
      tocLine("   7.3 Diabetes", 9),
      tocLine("   7.4 Cross-Disease Comparison", 10),
      tocLine("8. Discussion", 10),
      tocLine("9. Limitations", 11),
      tocLine("10. Future Scope", 12),
      tocLine("11. Conclusion", 12),
      tocLine("12. References", 12),
      new Paragraph({ children: [new PageBreak()] }),

      // Abstract
      h1("Abstract"),
      p("Quantum machine learning (QML) has been proposed as a candidate approach for extracting patterns from complex, high-dimensional data by exploiting superposition and entanglement to construct feature spaces that are difficult to represent classically. This project builds a scalable, hybrid quantum-classical framework for disease prediction and evaluates it across three heterogeneous medical diagnosis tasks: heart disease, diabetes, and breast cancer classification. A shared preprocessing and quantum-encoding pipeline is used across all three diseases, feeding into three model families: classical baselines (logistic regression, support vector machines), a fully variational quantum classifier (VQC) trained end-to-end via quantum gradients, and a hybrid quantum-kernel method that uses simulated quantum state overlaps as a kernel for a classical support vector machine. Across all three diseases, classical models remain highly competitive, the hybrid quantum kernel matches or slightly exceeds classical performance on two of three datasets, and the VQC shows a distinct behavior on the imbalanced diabetes dataset, trading recall for accuracy. These results, obtained on quantum circuit simulators rather than physical quantum hardware, illustrate both the promise and the current practical limitations of QML for clinical prediction tasks, and motivate a concrete roadmap for extending the framework to additional diseases, real quantum hardware, and clinically-validated deployment."),

      h1("1. Introduction"),
      p("Early and accurate diagnosis is one of the highest-leverage applications of machine learning in healthcare. Classical machine learning models — logistic regression, support vector machines, gradient-boosted trees, and neural networks — are already widely used for disease risk prediction from structured clinical data. Quantum machine learning proposes an alternative computational substrate: by encoding classical data into the amplitudes or rotation angles of qubits, a quantum circuit can, in principle, access an exponentially large Hilbert space with a comparatively small number of physical qubits, potentially uncovering feature correlations that are expensive to represent classically."),
      p("This project does not assume that quantum methods currently outperform classical ones on real clinical data — indeed, one of its explicit goals is to measure whether they do, honestly, on real datasets. Instead, it treats QML as one modeling option, sitting alongside classical baselines, within a single, reusable, multi-disease prediction pipeline. Rather than building a one-off model for a single disease, the project asks a broader engineering question: what does it take to build a framework where a new disease dataset can be plugged in, and classical, quantum, and hybrid models are trained and compared automatically? This framing was chosen deliberately, following the project's guiding principle: keep the underlying pipeline constant, and vary only the dataset and disease-specific configuration."),
      p("The remainder of this report is organized as follows. Section 2 introduces the necessary quantum computing and QML background. Section 3 briefly surveys related work. Section 4 describes the three datasets used. Section 5 presents the system architecture. Section 6 details the methodology for each model family. Section 7 reports experimental results. Section 8 discusses findings and their implications. Section 9 lists limitations, Section 10 lays out future scope, and Section 11 concludes."),

      h1("2. Background"),
      h2("2.1 Qubits, Superposition, and Entanglement"),
      p("A classical bit holds a value of 0 or 1. A qubit's state is instead a normalized vector in a two-dimensional complex Hilbert space, and can exist in a superposition of both basis states simultaneously. When multiple qubits are combined and entangled via two-qubit gates (such as CNOT), the joint system's state cannot be factored into independent single-qubit states, and the dimension of the space needed to describe it grows as 2^n for n qubits. This exponential scaling is the central resource that QML algorithms attempt to exploit — and also the reason that classically simulating more than a few dozen qubits becomes computationally intractable, which is why this project restricts itself to 4-qubit circuits that can be simulated exactly and quickly."),
      h2("2.2 Quantum Feature Maps and Angle Encoding"),
      p("Before a quantum circuit can process classical data, that data must be encoded into a quantum state. This project uses angle encoding: each classical feature value is mapped to a rotation angle of a single-qubit gate (specifically RY), so that a 4-dimensional classical feature vector is encoded onto 4 qubits. A layer of entangling CNOT gates is applied after the rotations so that the encoded state captures correlations between features rather than treating them as independent. This encoding strategy, and the closely related concept of a 'quantum feature Hilbert space', is discussed in Schuld and Killoran's work on quantum machine learning in feature Hilbert spaces."),
      h2("2.3 Variational Quantum Classifiers"),
      p("A variational quantum classifier (VQC) is a parameterized quantum circuit whose gate rotation angles are treated as trainable parameters, analogous to the weights of a classical neural network layer. After the data is encoded, a variational ansatz — alternating single-qubit rotations and entangling gates — is applied, and a measurement (here, the expectation value of the Pauli-Z operator on one qubit) produces a scalar output used for classification. Because the circuit is differentiable via the parameter-shift rule, its parameters can be optimized with gradient-based optimizers in much the same way as a classical model, despite the underlying computation being quantum. This architecture follows the circuit-centric quantum classifier design described by Schuld, Bocharov, Svore, and Wiebe, and the broader near-term quantum neural network approach proposed by Farhi and Neven."),
      h2("2.4 Quantum Kernel Methods"),
      p("An alternative to training a variational circuit end-to-end is to use the quantum feature map purely as a similarity measure: encode two classical data points into quantum states and compute the squared overlap (fidelity) between them. This overlap serves as a kernel function, which can then be plugged into a classical kernel method such as a support vector machine, without ever training quantum circuit parameters. This approach — used as the 'hybrid' model in this project — was introduced by Havlicek et al. in their work on supervised learning with quantum-enhanced feature spaces, and is generally considered more robust to the limited circuit depths available on near-term quantum hardware."),
      h2("2.5 The NISQ Constraint"),
      p("All experiments in this project are run on a classical simulator (PennyLane's default.qubit device) rather than physical quantum hardware. This is standard practice in current QML research: real quantum devices remain in what Preskill termed the Noisy Intermediate-Scale Quantum (NISQ) era, characterized by limited qubit counts, short coherence times, and gate errors that accumulate quickly with circuit depth. Simulation removes hardware noise entirely, which means the results reported here represent an idealized upper bound on what the same circuits would achieve on real quantum hardware today."),

      h1("3. Related Work"),
      p("Quantum machine learning for healthcare applications is an active but still early-stage research area. Variational quantum classifiers and quantum kernel methods, as described above, form the two dominant paradigms for near-term supervised QML, and both have been applied experimentally to small tabular biomedical datasets — including breast cancer and heart disease diagnosis — in the broader QML literature, generally reporting performance comparable to, but not decisively better than, classical baselines at current qubit counts. This project's contribution is not a novel quantum algorithm, but a reusable, multi-disease evaluation framework that applies the same encoding and training pipeline across three different diagnostic tasks, enabling a fair, side-by-side comparison of classical, quantum, and hybrid approaches under identical conditions."),

      h1("4. Datasets"),
      p("Three publicly available, well-established medical datasets were selected to represent distinct types of diagnostic problems: a small, feature-rich cardiology dataset (Heart Disease), a larger dataset with fewer, lifestyle-linked features and pronounced class imbalance (Diabetes), and a large, high-dimensional, cleanly separable diagnostic imaging-derived dataset (Breast Cancer)."),
      makeTable(
        ["Disease", "Samples", "Original Features", "Qubits Used", "PCA Variance Retained", "Positive (disease) rate"],
        datasetRows,
        [2200, 1200, 1800, 1200, 2000, 1600]
      ),
      caption("Table 1. Summary of the three disease datasets used in this project."),
      h2("4.1 Heart Disease (UCI / Cleveland)"),
      p("303 patient records with 13 clinical features including age, resting blood pressure, cholesterol, chest pain type, and maximum heart rate achieved, with a binary label indicating presence of heart disease."),
      h2("4.2 Diabetes (Pima Indians Diabetes Dataset)"),
      p("768 records with 8 features (glucose concentration, BMI, blood pressure, insulin, etc.) and a binary label for diabetes diagnosis. This dataset is notably imbalanced, with roughly 35% positive cases, and several features (e.g. insulin, skin thickness) contain a large number of zero values that likely represent missing data rather than true physiological zeros — a known characteristic of this dataset that affects downstream model performance."),
      h2("4.3 Breast Cancer (Wisconsin Diagnostic)"),
      p("569 records with 30 numeric features computed from digitized images of fine needle aspirate biopsies (e.g. mean radius, mean texture, mean concavity), with a binary label for malignant vs. benign diagnosis. This is among the cleanest and most separable datasets commonly used in binary medical classification benchmarks."),

      h1("5. System Architecture"),
      p("The framework is deliberately structured so that the pipeline logic — preprocessing, quantum encoding, model training, and evaluation — is shared across diseases, and only the data loader and a small set of configuration parameters change per disease. This makes it straightforward to extend the framework to additional diseases in the future (see Section 10) without rewriting the modeling logic."),
      image("architecture_diagram.png", 430, 470),
      caption("Figure 1. End-to-end architecture of the multi-disease QML framework."),

      h1("6. Methodology"),
      h2("6.1 Preprocessing Pipeline"),
      p("For each disease, features are first standardized (zero mean, unit variance) using a StandardScaler fit on the training split only. Principal Component Analysis (PCA) then reduces the feature space to 4 components — matching the 4-qubit budget used throughout this project — since simulating a variational quantum circuit's state vector scales as 2^n with the qubit count n, and larger qubit counts become computationally expensive to simulate classically. The 4 PCA components are then min-max scaled into the range [0, pi] radians, suitable for use as RY rotation angles."),
      p("It is worth noting explicitly that this dimensionality reduction step is lossy: as shown in Table 1, the 4 retained principal components capture between roughly 52% and 79% of the original variance depending on the disease, meaning the quantum and hybrid models are working with meaningfully less information than the classical baselines could access if given the full feature set. This is a direct, practical consequence of current quantum simulation and hardware constraints, and is discussed further in Section 8."),
      h2("6.2 Classical Baselines"),
      p("Logistic Regression and a Support Vector Machine with an RBF kernel were trained on the same 4-feature, PCA-reduced input as the quantum models, to ensure a fair, matched-feature comparison rather than an unfair comparison between a resource-constrained quantum model and a classical model with full feature access."),
      h2("6.3 Variational Quantum Classifier (VQC)"),
      p("The VQC uses angle embedding (Section 2.2) followed by 2 layers of a hardware-efficient variational ansatz: each layer applies an RY and RZ rotation to every qubit, followed by a ring of CNOT entangling gates. The output is the expectation value of Pauli-Z on the first qubit, shifted by a trainable bias, and trained by minimizing mean squared error against labels encoded as +1/-1, using the Nesterov Momentum optimizer (learning rate 0.25) with the parameter-shift rule for gradients. Training runs for 40 epochs with a batch size of 15, on a random subsample of up to 150 training examples per disease to keep simulation time tractable on classical hardware."),
      h2("6.4 Hybrid Quantum Kernel + SVM"),
      p("The hybrid model uses the same angle-embedding feature map, but does not train any quantum circuit parameters. Instead, the encoded quantum statevector is computed for every training and test example, and the squared inner product (fidelity) between pairs of statevectors forms a precomputed kernel matrix, which is passed to a classical SVM (sklearn's SVC with kernel='precomputed'). This is computationally far cheaper than the VQC, since it requires only one quantum circuit evaluation per data point rather than per point per training step."),
      h2("6.5 Experimental Setup"),
      makeTable(
        ["Parameter", "Value"],
        [
          ["Qubits", "4"],
          ["Variational layers", "2"],
          ["Training epochs (VQC)", "40"],
          ["Batch size (VQC)", "15"],
          ["Optimizer", "Nesterov Momentum, lr = 0.25"],
          ["Quantum simulator", "PennyLane default.qubit (exact statevector, no shot noise)"],
          ["Train / test split", "75% / 25%, stratified by label"],
          ["Random seed", "42 (fixed for reproducibility)"],
        ],
        [4000, 5000]
      ),
      caption("Table 2. Experimental configuration used across all three diseases."),

      h1("7. Results"),
      p("For each disease, all four models (Logistic Regression, SVM, VQC, and the Hybrid Quantum Kernel method) were trained and evaluated on an identical held-out test split. Table 3 reports accuracy, precision, recall, F1-score, and ROC-AUC for each model on each disease."),

      h2("7.1 Breast Cancer"),
      makeTable(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"], metricRow("Breast Cancer"), [2600, 1400, 1400, 1200, 1200, 1200]),
      caption("Table 3a. Results on the Breast Cancer dataset."),
      image("vqc_training_breast_cancer.png", 340, 227),
      caption("Figure 2. VQC training curve — Breast Cancer."),
      image("confusion_breast_cancer.png", 460, 155),
      caption("Figure 3. Confusion matrices for all four models — Breast Cancer."),

      h2("7.2 Heart Disease"),
      makeTable(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"], metricRow("Heart Disease"), [2600, 1400, 1400, 1200, 1200, 1200]),
      caption("Table 3b. Results on the Heart Disease dataset."),
      image("vqc_training_heart_disease.png", 340, 227),
      caption("Figure 4. VQC training curve — Heart Disease."),
      image("confusion_heart_disease.png", 460, 155),
      caption("Figure 5. Confusion matrices for all four models — Heart Disease."),

      h2("7.3 Diabetes"),
      makeTable(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"], metricRow("Diabetes"), [2600, 1400, 1400, 1200, 1200, 1200]),
      caption("Table 3c. Results on the Diabetes dataset."),
      image("vqc_training_diabetes.png", 340, 227),
      caption("Figure 6. VQC training curve — Diabetes."),
      image("confusion_diabetes.png", 460, 155),
      caption("Figure 7. Confusion matrices for all four models — Diabetes."),

      h2("7.4 Cross-Disease Comparison"),
      image("cross_disease_comparison.png", 470, 271),
      caption("Figure 8. Test accuracy of all four models across all three diseases."),

      h1("8. Discussion"),
      h2("8.1 Classical models remain strongest on Breast Cancer"),
      p("On Breast Cancer, Logistic Regression achieved the highest accuracy (97.2%) and the Hybrid Quantum Kernel method was close behind (95.8%), while the VQC lagged notably (86.7%), driven by low recall (64.2%) despite perfect precision — indicating the VQC's decision boundary is more conservative, only confidently flagging clear-cut malignant cases. Given that Breast Cancer is a nearly linearly separable dataset even in its raw feature space, this result is consistent with the expectation that classical linear and kernel methods should do very well here, and quantum methods offer no particular advantage on data of this structure."),
      h2("8.2 The Hybrid method is the most consistently competitive quantum-adjacent approach"),
      p("Across all three diseases, the Hybrid Quantum Kernel method tracked classical performance closely, exactly matching Logistic Regression's accuracy and F1 on Heart Disease (77.6% accuracy, 0.813 F1 for both), and staying within a few points of classical methods on the other two diseases. This is a meaningful finding: because the hybrid method does not require training quantum circuit parameters (only computing a fixed encoding once per data point), it is both dramatically cheaper to train (well under a second, versus roughly 2.5-3 minutes for the VQC in this simulated setting) and more numerically stable than the fully variational approach."),
      h2("8.3 The VQC shows a distinct, imbalance-sensitive behavior on Diabetes"),
      p("On the Diabetes dataset, the VQC achieved the highest raw accuracy of any model (71.4%), which at first glance looks like a quantum advantage. However, its recall on the positive (diabetic) class was only 26.9% — meaning it correctly identified fewer than 1 in 3 actual diabetes cases, achieving high accuracy largely by predicting the majority 'no diabetes' class more often. All four models on this dataset struggled with the same class-imbalance issue (only 34.9% positive rate combined with noisy, zero-imputed features), but this result highlights an important, general point for medical AI: accuracy alone is a misleading metric on imbalanced clinical data, since a model can score well while missing most true positive cases. Precision, recall, and F1 must be examined together, particularly when the cost of missing a true diagnosis (a false negative) is clinically high."),
      h2("8.4 Effect of dimensionality reduction"),
      p("Because all quantum and hybrid models were restricted to 4 PCA components to keep simulation tractable, they operated on substantially less information than the original feature sets, particularly for Heart Disease (52.4% of variance retained from 13 features) and Diabetes (71.2% from 8 features), compared to Breast Cancer (79.2% from 30 features). This is a direct simulation constraint rather than a fundamental limitation of quantum computing itself: on real quantum hardware, or with more efficient amplitude-encoding strategies, substantially more features could in principle be encoded per qubit."),

      h1("9. Limitations"),
      bullet("All quantum circuits were run on an exact-statevector classical simulator, not physical quantum hardware, so no hardware noise, decoherence, or gate error was modeled — real NISQ devices would likely show degraded performance relative to these results."),
      bullet("The 4-qubit budget, driven by classical simulation cost, forces aggressive PCA dimensionality reduction that discards a substantial fraction of the original feature variance."),
      bullet("The VQC was trained on a random subsample of at most 150 training examples per disease (rather than the full training set) to keep per-epoch simulation time practical, which may understate its achievable performance."),
      bullet("Heart Disease (303 samples) and to a lesser extent Diabetes are small by modern machine learning standards, and results should be interpreted as indicative rather than conclusive."),
      bullet("The variational ansatz (2 layers, RY/RZ + ring CNOT entanglement) was fixed by design choice rather than selected via architecture search; a different ansatz depth or entanglement pattern could change results materially."),
      bullet("No hyperparameter tuning (grid search or Bayesian optimization) was performed for the classical baselines, which were run with largely default settings for a fair, simple comparison rather than to find each model's best possible configuration."),

      h1("10. Future Scope"),
      p("This project intentionally scoped Phase 1 to three diseases with a shared framework, so that the natural next step is horizontal expansion rather than a redesign. Planned future directions include:"),
      bullet("Additional diseases: extending the same data-loader interface to Parkinson's disease, Alzheimer's disease, chronic kidney disease, liver disease, stroke, and thyroid disease datasets."),
      bullet("Real quantum hardware: running the trained VQC and quantum kernel circuits on cloud-accessible quantum processors (e.g. via IBM Quantum or similar providers) to measure the real-world impact of hardware noise on the results reported here."),
      bullet("Explicit noise simulation: incorporating depolarizing or amplitude-damping noise channels into the simulator (e.g. via PennyLane's mixed-state device) to study robustness before committing to real hardware runs."),
      bullet("Explainability: adding feature-attribution methods (e.g. SHAP for the classical models, and gradient-based attribution for the quantum circuits) so that predictions can be traced back to which clinical features drove them — important for clinical trust and adoption."),
      bullet("Multi-disease unified interface: exploring whether a single model can output calibrated probabilities across multiple diseases simultaneously from a shared patient feature vector, versus maintaining separate disease-specific classifiers behind one interface, only if the underlying data genuinely supports joint modeling."),
      bullet("Larger, clinically-sourced datasets and formal clinical validation, in collaboration with medical practitioners, before any real-world deployment consideration."),
      bullet("Federated or privacy-preserving learning, allowing the framework to train across multiple hospitals' data without centralizing sensitive patient records."),

      h1("11. Conclusion"),
      p("This project implemented and evaluated a scalable, hybrid quantum-classical framework for multi-disease prediction across Heart Disease, Diabetes, and Breast Cancer, comparing classical baselines, a fully variational quantum classifier, and a quantum-kernel hybrid method under matched experimental conditions. The results are honest rather than triumphant: classical machine learning remains the strongest approach on the datasets and qubit budgets studied here, the quantum-kernel hybrid approach is the most consistently competitive quantum-adjacent method, and the pure variational quantum classifier shows interesting but imbalance-sensitive behavior that underscores the importance of looking beyond raw accuracy in medical prediction tasks. Rather than claiming a present-day quantum advantage, this work demonstrates a reusable engineering pattern — a shared preprocessing, encoding, and evaluation pipeline into which new diseases, models, and eventually real quantum hardware can be plugged — that provides a credible foundation for continued, rigorous investigation as quantum hardware matures."),

      h1("12. References"),
      p("[1] J. Preskill, \"Quantum Computing in the NISQ era and beyond,\" Quantum, vol. 2, p. 79, 2018."),
      p("[2] V. Havlicek et al., \"Supervised learning with quantum-enhanced feature spaces,\" Nature, vol. 567, pp. 209-212, 2019."),
      p("[3] M. Schuld and N. Killoran, \"Quantum machine learning in feature Hilbert spaces,\" Physical Review Letters, vol. 122, 040504, 2019."),
      p("[4] M. Schuld, A. Bocharov, K. M. Svore, and N. Wiebe, \"Circuit-centric quantum classifiers,\" Physical Review A, vol. 101, 032308, 2020."),
      p("[5] E. Farhi and H. Neven, \"Classification with Quantum Neural Networks on Near Term Processors,\" arXiv:1802.06002, 2018."),
      p("[6] V. Bergholm et al., \"PennyLane: Automatic differentiation of hybrid quantum-classical computations,\" arXiv:1811.04968, 2018."),
      p("[7] UCI Machine Learning Repository, \"Heart Disease Data Set,\" University of California, Irvine."),
      p("[8] W. H. Wolberg, W. N. Street, and O. L. Mangasarian, \"Breast Cancer Wisconsin (Diagnostic) Data Set,\" UCI Machine Learning Repository."),
      p("[9] National Institute of Diabetes and Digestive and Kidney Diseases, \"Pima Indians Diabetes Database.\""),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("QML_Multi_Disease_Prediction_Report.docx", buffer);
  console.log("Report written.");
});
