"""
ml/common/dataset.py
======================
Common dataset abstraction (Section 10 of the spec): every disease
dataset, however different its raw columns are, gets loaded into the
same shape so the rest of the pipeline doesn't care which disease it's
looking at.

Datasets live in `datasets/<disease>.csv` at the project root. No values
are invented here — missing-value handling is a separate, explicit step
in the preprocessor, not silently done at load time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")


@dataclass
class Dataset:
    key: str
    display_name: str
    X: np.ndarray
    y: np.ndarray
    feature_names: List[str]
    class_names: Tuple[str, str]  # (negative, positive)
    missing_value_columns: List[str]  # columns where a sentinel (0) means "missing"


def _path(filename: str) -> str:
    return os.path.join(DATASETS_DIR, filename)


def load_diabetes() -> Dataset:
    # Pima Indians Diabetes dataset — no header row in the source file.
    cols = [
        "pregnancies", "glucose", "blood_pressure", "skin_thickness",
        "insulin", "bmi", "diabetes_pedigree", "age", "outcome",
    ]
    df = pd.read_csv(_path("diabetes.csv"), header=None, names=cols)
    y = df["outcome"].values.astype(int)
    feature_names = [c for c in cols if c != "outcome"]
    X = df[feature_names].values.astype(float)

    # In this dataset, a recorded 0 in these physiological columns is a
    # known data-entry artifact meaning "not measured," not a true zero
    # (a blood pressure or BMI of 0 is not physiologically possible).
    # Flagging them here; the preprocessor treats them as missing rather
    # than the pipeline inventing a value silently.
    missing_value_columns = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]

    return Dataset(
        key="diabetes",
        display_name="Diabetes",
        X=X,
        y=y,
        feature_names=feature_names,
        class_names=("No diabetes", "Diabetes"),
        missing_value_columns=missing_value_columns,
    )


def load_heart() -> Dataset:
    # UCI Heart Disease dataset (Cleveland subset).
    df = pd.read_csv(_path("heart.csv"), encoding="utf-8-sig")
    y = (df["target"].values.astype(int) > 0).astype(int)
    feature_names = [c for c in df.columns if c != "target"]
    X = df[feature_names].values.astype(float)

    return Dataset(
        key="heart",
        display_name="Cardiovascular disease",
        X=X,
        y=y,
        feature_names=feature_names,
        class_names=("No heart disease", "Heart disease"),
        missing_value_columns=[],  # this copy of the dataset has no sentinel-missing columns
    )


def load_kidney() -> Dataset:
    # UCI Chronic Kidney Disease dataset (Rubini, Soundarapandian & Eswaran,
    # 2015; CC BY 4.0), via the complete-case copy redistributed at
    # https://lisds.github.io/textbook/data/chronic_kidney_disease.html —
    # 158 patients with no missing values, 24 clinical features + class.
    df = pd.read_csv(_path("kidney.csv"))

    binary_yes_no = {"yes": 1, "no": 0}
    binary_present = {"present": 1, "notpresent": 0}
    binary_normal = {"normal": 0, "abnormal": 1}
    binary_appetite = {"good": 0, "poor": 1}

    encoded = pd.DataFrame({
        "age": df["Age"],
        "blood_pressure": df["Blood Pressure"],
        "specific_gravity": df["Specific Gravity"],
        "albumin": df["Albumin"],
        "sugar": df["Sugar"],
        "red_blood_cells": df["Red Blood Cells"].map(binary_normal),
        "pus_cell": df["Pus Cell"].map(binary_normal),
        "pus_cell_clumps": df["Pus Cell clumps"].map(binary_present),
        "bacteria": df["Bacteria"].map(binary_present),
        "blood_glucose_random": df["Blood Glucose Random"],
        "blood_urea": df["Blood Urea"],
        "serum_creatinine": df["Serum Creatinine"],
        "sodium": df["Sodium"],
        "potassium": df["Potassium"],
        "hemoglobin": df["Hemoglobin"],
        "packed_cell_volume": df["Packed Cell Volume"],
        "white_blood_cell_count": df["White Blood Cell Count"],
        "red_blood_cell_count": df["Red Blood Cell Count"],
        "hypertension": df["Hypertension"].map(binary_yes_no),
        "diabetes_mellitus": df["Diabetes Mellitus"].map(binary_yes_no),
        "coronary_artery_disease": df["Coronary Artery Disease"].map(binary_yes_no),
        "appetite": df["Appetite"].map(binary_appetite),
        "pedal_edema": df["Pedal Edema"].map(binary_yes_no),
        "anemia": df["Anemia"].map(binary_yes_no),
    })

    feature_names = list(encoded.columns)
    X = encoded.values.astype(float)
    y = df["Class"].values.astype(int)  # 1 = ckd, 0 = notckd (already this convention)

    return Dataset(
        key="kidney",
        display_name="Kidney disease",
        X=X,
        y=y,
        feature_names=feature_names,
        class_names=("No kidney disease", "Kidney disease"),
        missing_value_columns=[],  # complete-case copy — no missing values to begin with
    )


DATASET_LOADERS = {
    "diabetes": load_diabetes,
    "heart": load_heart,
    "kidney": load_kidney,
}


def load_dataset(key: str) -> Dataset:
    if key not in DATASET_LOADERS:
        raise KeyError(
            f"No dataset registered for '{key}'. Available: {list(DATASET_LOADERS)}"
        )
    return DATASET_LOADERS[key]()
