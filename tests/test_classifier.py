"""
Unit tests for IntentGuard classifier structure
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'intentguard'))

# We'll test the structure even if model doesn't exist yet
from intentguard.classifier.predict import predict_command, is_risky

class TestClassifier(unittest.TestCase):
    
    def test_predict_function_exists(self):
        """Test that predict_command function exists"""
        self.assertTrue(callable(predict_command))
        
    def test_is_risky_function_exists(self):
        """Test that is_risky function exists"""
        self.assertTrue(callable(is_risky))
        
    def test_model_path_constant(self):
        """Test that MODEL_PATH constant is defined"""
        from intentguard.classifier.predict import MODEL_PATH
        self.assertIsInstance(MODEL_PATH, str)
        
if __name__ == "__main__":
    unittest.main()