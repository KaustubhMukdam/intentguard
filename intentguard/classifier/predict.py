"""
Prediction script for IntentGuard classifier
Loads trained model and scores commands
"""

import joblib
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from intentguard.tokenizer import tokenize_command

MODEL_PATH = Path(__file__).parent / "model.joblib"


@lru_cache(maxsize=1)
def load_model():
    """Load the trained classifier (cached — model is immutable)."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Please run train.py first to train the model."
        )
    return joblib.load(MODEL_PATH)

def predict_command(command: str) -> dict:
    """
    Predict if a command is safe or risky

    Args:
        command: Command string to classify

    Returns:
        Dict with prediction and confidence
    """
    model = load_model()

    # Preprocess exactly as training does: shlex-tokenize then rejoin
    normalized = " ".join(tokenize_command(command))

    prediction = model.predict([normalized])[0]

    # LinearSVC confidence: sigmoid of decision_function (0-1 scale)
    decision_value = model.decision_function([normalized])[0]
    confidence = 1 / (1 + __import__("math").exp(-abs(decision_value)))

    return {
        "label": prediction,
        "confidence": float(confidence),
        "is_risky": prediction == "risky",
    }