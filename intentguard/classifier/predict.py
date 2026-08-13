"""
Prediction script for IntentGuard classifier
Loads trained model and scores commands
"""

import joblib
import os
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "model.joblib"

def load_model():
    """Load the trained classifier"""
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
    
    # Get prediction
    prediction = model.predict([command])[0]
    
    # Get probability/confidence if available
    try:
        # For LinearSVC, we can use decision function
        decision_value = model.decision_function([command])[0]
        # Convert to confidence-like score (0-1)
        # Using sigmoid approximation
        import math
        confidence = 1 / (1 + math.exp(-abs(decision_value)))
    except AttributeError:
        # Fallback if decision_function not available
        confidence = 0.8  # Default confidence
    
    return {
        "label": prediction,
        "confidence": float(confidence),
        "is_risky": prediction == "risky"
    }

def is_risky(command: str, threshold: float = 0.5) -> bool:
    """
    Quick check if command is risky
    
    Args:
        command: Command string to check
        threshold: Confidence threshold for risky classification
        
    Returns:
        True if command is predicted as risky with sufficient confidence
    """
    result = predict_command(command)
    return result["is_risky"] and result["confidence"] >= threshold

if __name__ == "__main__":
    # Test the predictor
    test_commands = [
        "ls -la",
        "rm -rf /tmp/test",
        "dd if=/dev/zero of=/dev/sda",
        "chmod 755 file.txt"
    ]
    
    for cmd in test_commands:
        result = predict_command(cmd)
        print(f"Command: {cmd}")
        print(f"  Prediction: {result['label']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Risky: {result['is_risky']}")
        print()