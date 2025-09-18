#!/usr/bin/env python3
"""
Simple test script for enhanced document processing API.
Tests the valueArray error fix with a real PDF.
"""

import requests
import time
import json
import os

def test_enhanced_processing():
    """Test the enhanced document processing API."""
    
    print("🧪 Testing Enhanced Document Processing API...")
    print("📍 Server: http://localhost:8000")
    
    # Check if server is responding
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"✅ Server is responding (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Test with sample PDF
    pdf_path = "data/sample_layout.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    print(f"📄 Testing with: {pdf_path}")
    
    # Submit processing job
    print("📤 Submitting processing job...")
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            data = {'custom_filename': 'test_sample_layout'}
            
            response = requests.post(
                "http://localhost:8000/enhanced/process",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Job submitted successfully! Job ID: {job_id}")
            
            # Monitor job status
            print("⏳ Monitoring job progress...")
            max_attempts = 60  # Wait up to 10 minutes
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    status_response = requests.get(f"http://localhost:8000/enhanced/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data['status']
                        
                        if status == 'completed':
                            print(f"🎉 Processing completed successfully!")
                            print(f"📊 Results: {json.dumps(status_data['result'], indent=2)}")
                            return True
                        elif status == 'failed':
                            print(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                            return False
                        else:
                            print(f"⏳ Status: {status}... (attempt {attempt + 1}/{max_attempts})")
                            time.sleep(10)
                    else:
                        print(f"❌ Failed to get status: {status_response.status_code}")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error checking status: {e}")
                    return False
                
                attempt += 1
            
            print(f"⏰ Timeout waiting for job completion")
            return False
            
        else:
            print(f"❌ Failed to submit job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_processing()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ The valueArray error fix is working correctly!")
    else:
        print("\n💥 Test failed!")
        print("❌ Check the server logs for more details.")