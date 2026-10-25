"""
data_loaders.py
================
Common interface: each loader returns (X, y, feature_names, disease_name, class_names)
  X: (n_samples, n_features) numpy array, all numeric
  y: (n_samples,) numpy array, 0/1 binary label (1 = disease present)
  class_names: (negative_label, positive_label)
"""

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer


def load_breast_cancer_data():
    data = load_breast_cancer()
    X, y = data.data, data.target
    # sklearn encodes 0=malignant, 1=benign -> flip so 1 = disease present (malignant)
    y = 1 - y
    return X, y, list(data.feature_names), "Breast Cancer", ("No Cancer (Benign)", "Cancer (Malignant)")


def load_heart_disease_data(path="data/heart.csv"):
    df = pd.read_csv(path, encoding="utf-8-sig")
    y = df["target"].values.astype(int)
    X = df.drop(columns=["target"]).values.astype(float)
    feature_names = [c for c in df.columns if c != "target"]
    return X, y, feature_names, "Heart Disease", ("No Heart Disease", "Heart Disease")


def load_diabetes_data(path="data/diabetes.csv"):
    cols = ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
            "insulin", "bmi", "diabetes_pedigree", "age", "outcome"]
    df = pd.read_csv(path, header=None, names=cols)
    y = df["outcome"].values.astype(int)
    X = df.drop(columns=["outcome"]).values.astype(float)
    feature_names = [c for c in cols if c != "outcome"]
    return X, y, feature_names, "Diabetes", ("No Diabetes", "Diabetes")


DISEASE_LOADERS = {
    "breast_cancer": load_breast_cancer_data,
    "heart_disease": load_heart_disease_data,
    "diabetes": load_diabetes_data,
}


if __name__ == "__main__":
    for key, loader in DISEASE_LOADERS.items():
        X, y, feat, name, classes = loader()
        print(f"{name:15s} | X={X.shape} | positive rate={y.mean():.3f} | features={len(feat)}")
