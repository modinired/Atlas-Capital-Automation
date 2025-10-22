#!/usr/bin/env python
"""
Evaluate demographic parity on a trained model.

This script computes basic fairness metrics for a binary classifier by comparing
the average predicted probability across groups defined by a sensitive
attribute.  It does not rely on any third‑party libraries and is intended for
illustrative purposes only.  For comprehensive fairness analysis, use
specialized frameworks such as AIF360.

Expected CSV columns:

    debt_to_income,credit_utilization,age_years,savings_ratio,has_delinquency,
    label,sensitive

Where `sensitive` is a binary attribute (e.g. gender or ethnicity indicator).

Usage:

    python evaluate_fairness.py --data test.csv --model model.pkl

Author: Terry Delmonaco Presents: AI Team
"""
from __future__ import annotations

import argparse
import csv
import json
import pickle
from typing import List, Tuple


def load_data(path: str) -> Tuple[List[List[float]], List[int], List[int]]:
    xs: List[List[float]] = []
    ys: List[int] = []
    groups: List[int] = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            xs.append([
                float(row["debt_to_income"]),
                float(row["credit_utilization"]),
                float(row["age_years"]),
                float(row["savings_ratio"]),
                float(row["has_delinquency"]),
            ])
            ys.append(int(row["label"]))
            groups.append(int(row["sensitive"]))
    return xs, ys, groups


def load_model(path: str) -> Tuple[List[float], float]:
    with open(path, "rb") as f:
        obj = pickle.load(f)
    weights = [
        obj["weights"]["debt_to_income"],
        obj["weights"]["credit_utilization"],
        obj["weights"]["age_years"],
        obj["weights"]["savings_ratio"],
        obj["weights"]["has_delinquency"],
    ]
    bias = obj["bias"]
    return weights, bias


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + pow(2.718281828459045, -z))


def compute_probabilities(xs: List[List[float]], weights: List[float], bias: float) -> List[float]:
    probs: List[float] = []
    for x_vec in xs:
        z = bias + sum(w * x for w, x in zip(weights, x_vec))
        probs.append(sigmoid(z))
    return probs


def evaluate_demographic_parity(probs: List[float], groups: List[int]) -> None:
    group0 = [p for p, g in zip(probs, groups) if g == 0]
    group1 = [p for p, g in zip(probs, groups) if g == 1]
    avg0 = sum(group0) / len(group0) if group0 else 0.0
    avg1 = sum(group1) / len(group1) if group1 else 0.0
    diff = abs(avg0 - avg1)
    print(f"Average probability for group 0: {avg0:.4f}")
    print(f"Average probability for group 1: {avg1:.4f}")
    print(f"Absolute difference (demographic parity gap): {diff:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model fairness.")
    parser.add_argument("--data", required=True, help="Path to evaluation CSV file")
    parser.add_argument("--model", required=True, help="Path to model pickle file")
    args = parser.parse_args()
    xs, ys, groups = load_data(args.data)
    weights, bias = load_model(args.model)
    probs = compute_probabilities(xs, weights, bias)
    evaluate_demographic_parity(probs, groups)


if __name__ == "__main__":
    main()