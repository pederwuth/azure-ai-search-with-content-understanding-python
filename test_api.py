#!/usr/bin/env python3
"""
Test the enhanced document processing API with a sample PDF.
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_enhanced_processing():
    """Test the enhanced processing API endpoint."""
    
    api_base = "http://localhost:8000"
    
    # Test with a sample PDF
    sample_pdf = "/workspaces/azure-ai-search-with-content-understanding-python/data/sample_layout.pdf"
    
    if not Path(sample_pdf).exists():
        print(f"❌ Sample PDF not found: {sample_pdf}")
        return False
    
    print("🚀 Testing Enhanced Document Processing API...")
    print(f"📄 Processing: {sample_pdf}")
    
    try:
        # Submit processing job
        with open(sample_pdf, 'rb') as f:
            files = {'file': f}
            data = {'custom_filename': 'test_sample_layout_api'}
            
            print("📤 Submitting processing job...")
            response = requests.post(f"{api_base}/enhanced/process", files=files, data=data)
            
            if response.status_code != 200:
                print(f"❌ API request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Job submitted: {job_id}")
        
        # Poll for status
        print("⏳ Polling for job completion...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{api_base}/enhanced/status/{job_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            status = status_data['status']
            
            print(f"📊 Status: {status}")
            
            if status == 'completed':
                print("✅ Processing completed successfully!")
                print(f"📈 Results:")
                result = status_data['result']
                print(f"   - Document length: {result.get('document_length', 'N/A'):,} characters")
                print(f"   - Figures processed: {result.get('processing_stats', {}).get('figures_processed', 'N/A')}")
                print(f"   - Estimated tokens: {result.get('processing_stats', {}).get('estimated_tokens', 'N/A'):,}")
                print(f"   - Enhanced markdown: {result.get('enhanced_markdown_path', 'N/A')}")
                return True
                
            elif status == 'failed':
                print(f"❌ Processing failed!")
                if 'error' in status_data:
                    print(f"   Error: {status_data['error']}")
                return False
            
            # Wait before next poll
            time.sleep(5)
        
        print("⏰ Processing timed out")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_processing()
    
    if success:
        print("\n🎉 API test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 API test failed!")
        sys.exit(1)