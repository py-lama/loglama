"""
Basic tests for the package
"""
import unittest
import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestBasic(unittest.TestCase):
    """Basic tests for the package"""
    
    def test_import(self):
        """Test that the package can be imported"""
        try:
            # Try to import the package (will be replaced with actual package name)
            import loglama
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import package")

if __name__ == "__main__":
    unittest.main()
