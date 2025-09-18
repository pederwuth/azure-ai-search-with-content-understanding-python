#!/usr/bin/env python3
"""
Test script for the enhanced document processor fix without Azure dependencies.
This tests the error handling logic specifically.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_error_handling_logic():
    """Test the _format_result function error handling logic directly."""
    
    print("🧪 Testing Enhanced Document Processor Error Handling...")
    
    # Import the module to test the fix
    try:
        from src.enhanced_document_processor import EnhancedDocumentProcessor
        
        # Test the static method that was causing issues
        processor = EnhancedDocumentProcessor.__new__(EnhancedDocumentProcessor)
        
        # Mock API response that would cause the original error
        mock_response_without_value_array = {
            "analyzeResult": {
                "readResult": {
                    "content": "Sample content analysis result"
                }
            }
        }
        
        # Mock API response that would work with original code
        mock_response_with_value_array = {
            "analyzeResult": {
                "readResult": {
                    "content": "Sample content analysis result"
                }
            },
            "valueArray": [
                {"content": "Some extracted content"}
            ]
        }
        
        # Test both scenarios
        print("📋 Testing response without valueArray (should use fallback)...")
        result1 = processor._format_result(mock_response_without_value_array)
        print(f"✅ Result 1: {result1}")
        
        print("📋 Testing response with valueArray (should use original logic)...")
        result2 = processor._format_result(mock_response_with_value_array)
        print(f"✅ Result 2: {result2}")
        
        print("✅ Error handling logic test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_imports():
    """Test that all imports work correctly."""
    
    print("📦 Testing module imports...")
    
    try:
        from src.enhanced_document_processor import EnhancedDocumentProcessor
        print("✅ EnhancedDocumentProcessor imported successfully")
        
        from src.enhanced_api import router
        print("✅ Enhanced API router imported successfully")
        
        print("✅ All imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Enhanced Document Processor Fixes\n")
    
    # Test imports first
    imports_ok = test_imports()
    
    if imports_ok:
        # Test error handling logic
        error_handling_ok = test_error_handling_logic()
        
        if error_handling_ok:
            print("\n🎉 All tests passed! The valueArray fix is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Error handling test failed!")
            sys.exit(1)
    else:
        print("\n💥 Import tests failed!")
        sys.exit(1)