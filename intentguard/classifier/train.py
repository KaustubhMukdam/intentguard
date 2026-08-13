"""
Training script for IntentGuard classifier
Trains TF-IDF + LinearSVC on labeled dataset
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import joblib
import os
from pathlib import Path

def load_dataset(data_path: str = "../../data/commands_dataset.csv"):
    """Load the labeled command dataset"""
    df = pd.read_csv(data_path)
    return df['command'].tolist(), df['label'].tolist()

def create_pipeline():
    """Create TF-IDF + LinearSVC pipeline"""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 4),
            lowercase=True
        )),
        ('clf', LinearSVC(
            class_weight='balanced',
            dual=False,
            max_iter=1000
        ))
    ])

def train_model(X, y, model_path: str = "./model.joblib"):
    """Train the classifier and save it"""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create and train pipeline
    pipeline = create_pipeline()
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    f1 = f1_score(y_test, y_pred, pos_label='risky')
    
    print(f"F1-score (risky class): {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved to {model_path}")
    
    return pipeline, f1

def main():
    """Main training function"""
    # Load data
    print("Loading dataset...")
    X, y = load_dataset()
    print(f"Loaded {len(X)} commands ({sum(1 for label in y if label == 'risky')} risky, {sum(1 for label in y if label == 'safe')} safe)")
    
    # Train model
    print("\nTraining model...")
    model, f1_score = train_model(X, y)
    
    return model, f1_score

if __name__ == "__main__":
    main()