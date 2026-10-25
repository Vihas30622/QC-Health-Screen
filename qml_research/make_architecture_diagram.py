import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(9, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 15)
ax.axis("off")

def box(x, y, w, h, text, color="#EDE7F6", fontsize=9, edge="#5E35B1"):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                        linewidth=1.4, edgecolor=edge, facecolor=color)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize, wrap=True)

def arrow(x1, y1, x2, y2):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                         linewidth=1.3, color="#444444")
    ax.add_patch(a)

# Patient data
box(3, 13.6, 4, 0.9, "Patient Medical Data\n(raw clinical features)", color="#FFF3E0", edge="#EF6C00")
arrow(5, 13.6, 5, 13.0)

# Disease selection
box(3, 12.2, 4, 0.7, "Disease Selection", color="#E3F2FD", edge="#1565C0")
arrow(5, 12.2, 5, 11.7)

# Three branches
box(0.3, 10.6, 2.8, 0.8, "Heart Disease\n(UCI, 13 features)", fontsize=8.5)
box(3.6, 10.6, 2.8, 0.8, "Diabetes\n(Pima, 8 features)", fontsize=8.5)
box(6.9, 10.6, 2.8, 0.8, "Breast Cancer\n(Wisconsin, 30 features)", fontsize=8.5)
arrow(5, 11.7, 1.7, 11.4)
arrow(5, 11.7, 5, 11.4)
arrow(5, 11.7, 8.3, 11.4)

for cx in [1.7, 5, 8.3]:
    arrow(cx, 10.6, cx, 10.0)

# preprocessing row
box(0.3, 9.2, 2.8, 0.8, "Preprocess +\nFeature Scaling", fontsize=8.5)
box(3.6, 9.2, 2.8, 0.8, "Preprocess +\nFeature Scaling", fontsize=8.5)
box(6.9, 9.2, 2.8, 0.8, "Preprocess +\nFeature Scaling", fontsize=8.5)
for cx in [1.7, 5, 8.3]:
    arrow(cx, 9.2, cx, 8.6)

box(0.3, 7.8, 2.8, 0.8, "PCA -> 4 features\n(qubit budget)", fontsize=8.5)
box(3.6, 7.8, 2.8, 0.8, "PCA -> 4 features\n(qubit budget)", fontsize=8.5)
box(6.9, 7.8, 2.8, 0.8, "PCA -> 4 features\n(qubit budget)", fontsize=8.5)
for cx in [1.7, 5, 8.3]:
    arrow(cx, 7.8, cx, 7.2)

# merge into common framework
arrow(1.7, 7.2, 5, 6.6)
arrow(5, 7.2, 5, 6.6)
arrow(8.3, 7.2, 5, 6.6)

box(2.5, 5.8, 5, 0.9, "Common QML Framework\n(shared angle-encoding pipeline)", color="#E8EAF6", edge="#3949AB")
arrow(5, 5.8, 5, 5.2)

# three model branches
box(0.3, 4.2, 2.8, 0.9, "Classical Baseline\nLogistic Regression / SVM", fontsize=8, color="#FFEBEE", edge="#C62828")
box(3.6, 4.2, 2.8, 0.9, "Quantum (VQC)\nVariational circuit,\ntrained end-to-end", fontsize=8, color="#EDE7F6", edge="#6A1B9A")
box(6.9, 4.2, 2.8, 0.9, "Hybrid\nQuantum kernel + SVM", fontsize=8, color="#E0F2F1", edge="#00695C")
arrow(5, 5.2, 1.7, 5.1)
arrow(5, 5.2, 5, 5.1)
arrow(5, 5.2, 8.3, 5.1)
for cx in [1.7, 5, 8.3]:
    arrow(cx, 4.2, cx, 3.6)

arrow(1.7, 3.6, 5, 3.0)
arrow(5, 3.6, 5, 3.0)
arrow(8.3, 3.6, 5, 3.0)

box(2.7, 2.2, 4.6, 0.8, "Metrics & Evaluation\n(accuracy, precision, recall, F1, ROC-AUC)", fontsize=8.5, color="#FFF8E1", edge="#F9A825")
arrow(5, 2.2, 5, 1.6)

box(2.7, 0.7, 4.6, 0.9, "Disease Prediction Output\n(per-disease diagnosis + confidence)", color="#E8F5E9", edge="#2E7D32")

plt.title("Scalable Hybrid Quantum-Classical\nMulti-Disease Prediction Framework", fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig("architecture_diagram.png", dpi=150, bbox_inches="tight")
print("saved")
