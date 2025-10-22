#!/usr/bin/env python
"""
Train a logistic regression model for Terry Delmonaco Presents: AI.

This script implements a simple logistic regression learner using batch
gradient descent and pure Python (no external libraries).  It reads a CSV
file containing credit features and a binary label, trains a model, and
serializes the model to a pickle file.  The training algorithm is intended
for small to medium datasets; for large datasets or production training,
consider using optimized libraries such as scikit‑learn.

Expected CSV columns:

    debt_to_income,credit_utilization,age_years,savings_ratio,has_delinquency,label

Usage:

    python train_model.py --data training.csv --output model.pkl --epochs 1000 --lr 0.01

Author: Terry Delmonaco Presents: AI Team
"""
from __future__ import annotations

import argparse
import csv
import math
import pickle
from typing import List, Tuple


def load_data(path: str) -> Tuple[List[List[float]], List[int]]:
    """Load feature vectors and labels from a CSV file."""
    xs: List[List[float]] = []
    ys: List[int] = []
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
    return xs, ys


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))


def train_logistic_regression(
    xs: List[List[float]], ys: List[int], epochs: int = 1000, lr: float = 0.01
) -> Tuple[List[float], float]:
    """Train logistic regression weights and bias using batch gradient descent."""
    n_features = len(xs[0])
    n_samples = len(xs)
    # Initialize weights and bias to zeros
    weights = [0.0 for _ in range(n_features)]
    bias = 0.0
    for epoch in range(epochs):
        grad_w = [0.0 for _ in range(n_features)]
        grad_b = 0.0
        for x_vec, y_true in zip(xs, ys):
            # Linear combination
            z = bias + sum(w * x for w, x in zip(weights, x_vec))
            y_hat = sigmoid(z)
            error = y_hat - y_true
            for j in range(n_features):
                grad_w[j] += error * x_vec[j]
            grad_b += error
        # Update weights and bias
        for j in range(n_features):
            weights[j] -= lr * grad_w[j] / n_samples
        bias -= lr * grad_b / n_samples
    return weights, bias


def save_model(weights: List[float], bias: float, output_path: str) -> None:
    """Serialize the logistic regression model to a pickle file."""
    model = {
        "weights": {
            "debt_to_income": weights[0],
            "credit_utilization": weights[1],
            "age_years": weights[2],
            "savings_ratio": weights[3],
            "has_delinquency": weights[4],
        },
        "bias": bias,
    }
    with open(output_path, "wb") as f:
        pickle.dump(model, f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a logistic regression model.")
    parser.add_argument("--data", required=True, help="Path to training CSV file")
    parser.add_argument("--output", required=True, help="Path to output pickle file")
    parser.add_argument("--epochs", type=int, default=1000, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    args = parser.parse_args()
    xs, ys = load_data(args.data)
    weights, bias = train_logistic_regression(xs, ys, epochs=args.epochs, lr=args.lr)
    save_model(weights, bias, args.output)
    print(f"Trained model saved to {args.output}")


if __name__ == "__main__":
    main()