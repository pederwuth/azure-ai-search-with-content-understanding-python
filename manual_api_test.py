#!/usr/bin/env python3
"""
Manual API testing script with interactive options.
"""

import requests
import time
import json
from pathlib import Path

def test_api_manual():
    """Manual API testing with different options."""
    
    base_url = "http://localhost:8000"
    
    print("🌐 Manual API Testing")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("❌ API server not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("💡 Start the server with: python api_server.py")
        return
    
    # List available files
    available_files = []
    data_dir = Path("data")
    if data_dir.exists():
        available_files = list(data_dir.glob("*.pdf"))
    
    print(f"\n📁 Available PDFs in data/ directory:")
    for i, pdf_file in enumerate(available_files, 1):
        print(f"   {i}. {pdf_file.name}")
    
    # Get analyzer templates
    try:
        response = requests.get(f"{base_url}/analyzer-templates")
        templates = response.json()
        print(f"\n🔧 Available analyzer templates:")
        for template in templates:
            print(f"   - {template['name']}")
    except Exception as e:
        print(f"❌ Could not get templates: {e}")
        return
    
    print("\n" + "=" * 50)
    
    while True:
        try:
            # Select PDF
            choice = input(f"\n📄 Select PDF (1-{len(available_files)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            pdf_index = int(choice) - 1
            if 0 <= pdf_index < len(available_files):
                selected_pdf = available_files[pdf_index]
                
                # Get options
                template = input("🔧 Analyzer template (default: content_document): ").strip()
                if not template:
                    template = "content_document"
                
                generate_summary = input("📝 Generate summary? (y/N): ").strip().lower() == 'y'
                
                print(f"\n🚀 Processing {selected_pdf.name}...")
                print(f"   Template: {template}")
                print(f"   Summary: {generate_summary}")
                print("-" * 30)
                
                # Upload and process
                with open(selected_pdf, 'rb') as f:
                    files = {'file': (selected_pdf.name, f, 'application/pdf')}
                    data = {
                        'analyzer_template': template,
                        'generate_summary': generate_summary
                    }
                    
                    response = requests.post(f"{base_url}/process-pdf", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        job_id = result['job_id']
                        print(f"✅ Job created: {job_id}")
                        
                        # Poll for completion
                        print("⏳ Waiting for completion...")
                        while True:
                            status_response = requests.get(f"{base_url}/jobs/{job_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                print(f"   Status: {status_data['status']} - {status_data['progress']}% - {status_data['message']}")
                                
                                if status_data['status'] in ['completed', 'failed']:
                                    break
                                    
                                time.sleep(2)
                            else:
                                print("❌ Failed to get job status")
                                break
                        
                        if status_data['status'] == 'completed':
                            print("\n✅ Processing completed!")
                            
                            # Download results
                            markdown_response = requests.get(f"{base_url}/jobs/{job_id}/download/markdown")
                            if markdown_response.status_code == 200:
                                filename = f"manual_result_{job_id}.md"
                                with open(filename, 'w', encoding='utf-8') as f:
                                    f.write(markdown_response.text)
                                print(f"📝 Downloaded: {filename}")
                                
                                # Show preview
                                content = markdown_response.text
                                print(f"\n📖 Content preview ({len(content)} chars):")
                                print("-" * 40)
                                print(content[:500] + "..." if len(content) > 500 else content)
                            
                        else:
                            print(f"❌ Processing failed: {status_data.get('message', 'Unknown error')}")
                    
                    else:
                        print(f"❌ Upload failed: {response.status_code} - {response.text}")
            
            else:
                print(f"❌ Invalid selection. Please choose 1-{len(available_files)}.")
                
        except ValueError:
            print(f"❌ Please enter a number (1-{len(available_files)}) or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    test_api_manual()
