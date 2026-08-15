"""
Training script for IntentGuard classifier
Trains TF-IDF + LinearSVC on the labeled command dataset.

Usage:
    python -m intentguard.classifier.train                  # baseline (defaults)
    python -m intentguard.classifier.train --ngram 1 3      # tune n-gram range
    python -m intentguard.classifier.train --no-balance     # drop class_weight

Metrics focus (per eval.md): F1 and recall on the risky class.
"""

import argparse
import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from intentguard.tokenizer import tokenize_command

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = REPO_ROOT / "data" / "commands_dataset.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"


def load_dataset(data_path: Path = DEFAULT_DATA):
    """Load labeled commands; commands are shlex-tokenized then re-joined."""
    commands, labels = [], []
    with open(data_path, newline="") as f:
        for row in csv.DictReader(f):
            commands.append(" ".join(tokenize_command(row["command"])))
            labels.append(row["label"].strip().lower())
    return commands, labels


def create_pipeline(ngram_range=(2, 4), balanced=True):
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=ngram_range,
            lowercase=True,
        )),
        ("clf", LinearSVC(
            class_weight="balanced" if balanced else None,
            dual=False,
            max_iter=1000,
        )),
    ])


def train_model(X, y, model_path, ngram_range=(2, 4), balanced=True):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = create_pipeline(ngram_range, balanced)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(
        y_test, y_pred, labels=["safe", "risky"],
        target_names=["safe", "risky"], digits=4,
    )
    print(f"Configuration: ngram={ngram_range} class_weight={'balanced' if balanced else 'none'}")
    print(f"Test split: {len(X_test)} commands\n")
    print(report)

    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")
    return pipeline, report


def main():
    parser = argparse.ArgumentParser(description="Train IntentGuard risk classifier")
    parser.add_argument("--ngram", nargs=2, type=int, default=[2, 4], metavar=("MIN", "MAX"))
    parser.add_argument("--no-balance", action="store_true", help="disable class_weight='balanced'")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="path to commands_dataset.csv")
    args = parser.parse_args()

    X, y = load_dataset(args.data)
    n_risky = sum(1 for label in y if label == "risky")
    n_safe = sum(1 for label in y if label == "safe")
    print(f"Loaded {len(X)} commands ({n_risky} risky, {n_safe} safe) from {args.data}")

    train_model(
        X, y,
        model_path=MODEL_PATH,
        ngram_range=tuple(args.ngram),
        balanced=not args.no_balance,
    )


if __name__ == "__main__":
    main()
