#!/usr/bin/env python3
"""
Test client for Educational Content Understanding API.

This script demonstrates how to use the FastAPI server to process documents
with Content Understanding capabilities.
"""

import requests
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any

class ContentUnderstandingAPIClient:
    """Client for testing the Content Understanding API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_config(self) -> Dict[str, Any]:
        """Get API configuration status."""
        response = self.session.get(f"{self.base_url}/config")
        response.raise_for_status()
        return response.json()
    
    def list_analyzer_templates(self) -> Dict[str, Any]:
        """List available analyzer templates."""
        response = self.session.get(f"{self.base_url}/analyzer-templates")
        response.raise_for_status()
        return response.json()
    
    def process_pdf(
        self,
        pdf_path: str,
        analyzer_template: str = "content_document",
        generate_summary: bool = True,
        output_dir: str = None
    ) -> str:
        """
        Process a PDF file and return job ID.
        
        Args:
            pdf_path: Path to the PDF file
            analyzer_template: Analyzer template to use
            generate_summary: Whether to generate a summary
            output_dir: Output directory (optional)
            
        Returns:
            Job ID for tracking processing
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Prepare form data
        files = {'file': ('document.pdf', open(pdf_file, 'rb'), 'application/pdf')}
        data = {
            'analyzer_template': analyzer_template,
            'generate_summary': generate_summary
        }
        if output_dir:
            data['output_dir'] = output_dir
        
        try:
            response = self.session.post(
                f"{self.base_url}/process-pdf",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            return result['job_id']
        finally:
            files['file'][1].close()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job processing status."""
        response = self.session.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Wait for job completion with polling.
        
        Args:
            job_id: Job ID to monitor
            timeout: Maximum wait time in seconds
            
        Returns:
            Final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            print(f"Status: {status['status']} - {status['progress']}% - {status['message']}")
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            time.sleep(5)  # Poll every 5 seconds
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def download_result(self, job_id: str, file_type: str, output_path: str = None):
        """
        Download processing results.
        
        Args:
            job_id: Job ID
            file_type: Type of file to download ('markdown' or 'summary')
            output_path: Local path to save the file
        """
        response = self.session.get(f"{self.base_url}/jobs/{job_id}/download/{file_type}")
        response.raise_for_status()
        
        if not output_path:
            # Try to get filename from response headers
            content_disposition = response.headers.get('content-disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                output_path = filename
            else:
                output_path = f"result_{job_id}_{file_type}"
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded {file_type} to: {output_path}")
        return output_path
    
    def test_pipeline(self) -> Dict[str, Any]:
        """Test the pipeline with built-in sample."""
        response = self.session.post(f"{self.base_url}/test-pipeline")
        response.raise_for_status()
        return response.json()
    
    def list_jobs(self) -> Dict[str, Any]:
        """List all processing jobs."""
        response = self.session.get(f"{self.base_url}/jobs")
        response.raise_for_status()
        return response.json()

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Test Content Understanding API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--pdf-path", help="Path to PDF file to process")
    parser.add_argument("--analyzer-template", default="content_document", help="Analyzer template")
    parser.add_argument("--no-summary", action="store_true", help="Skip summary generation")
    parser.add_argument("--test-only", action="store_true", help="Only run pipeline test")
    parser.add_argument("--list-jobs", action="store_true", help="List all jobs")
    parser.add_argument("--job-status", help="Get status of specific job ID")
    parser.add_argument("--download", nargs=2, metavar=('JOB_ID', 'FILE_TYPE'), 
                       help="Download result (job_id file_type)")
    
    args = parser.parse_args()
    
    # Initialize client
    client = ContentUnderstandingAPIClient(args.base_url)
    
    try:
        # Health check
        print("🔍 Checking API health...")
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"📦 Pipeline Available: {health['pipeline_available']}")
        
        if not health['pipeline_available']:
            print("❌ Pipeline not available. Check server logs.")
            return
        
        # Configuration check
        print("\n🔧 Checking configuration...")
        config = client.get_config()
        print(f"⚙️  All Configured: {config['all_configured']}")
        for service, status in config['configuration'].items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {service}: {status}")
        
        # List analyzer templates
        print("\n📋 Available analyzer templates:")
        templates = client.list_analyzer_templates()
        for template in templates['templates']:
            print(f"   📄 {template['name']} ({template['filename']})")
        
        # Handle specific actions
        if args.list_jobs:
            print("\n📊 Listing all jobs...")
            jobs = client.list_jobs()
            for job in jobs['jobs']:
                print(f"   🔧 {job['job_id'][:8]}... - {job['status']} - {job['filename']}")
            return
        
        if args.job_status:
            print(f"\n📋 Getting status for job {args.job_status}...")
            status = client.get_job_status(args.job_status)
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress']}%")
            print(f"   Message: {status['message']}")
            return
        
        if args.download:
            job_id, file_type = args.download
            print(f"\n⬇️  Downloading {file_type} for job {job_id}...")
            output_path = client.download_result(job_id, file_type)
            print(f"✅ Downloaded to: {output_path}")
            return
        
        if args.test_only:
            print("\n🧪 Running pipeline test...")
            result = client.test_pipeline()
            print(f"✅ Test Status: {result['status']}")
            print(f"📄 Sample File: {result['sample_file']}")
            print(f"📊 Result: {result['message']}")
            if 'result' in result:
                print(f"   📝 Markdown Length: {result['result']['enhanced_markdown_length']:,} chars")
                print(f"   📁 Output: {result['result']['enhanced_markdown']}")
            return
        
        # Process PDF if provided
        if args.pdf_path:
            pdf_path = Path(args.pdf_path)
            if not pdf_path.exists():
                print(f"❌ PDF file not found: {args.pdf_path}")
                return
            
            print(f"\n📄 Processing PDF: {pdf_path}")
            print(f"🔧 Analyzer Template: {args.analyzer_template}")
            print(f"📝 Generate Summary: {not args.no_summary}")
            
            # Submit processing job
            job_id = client.process_pdf(
                pdf_path=str(pdf_path),
                analyzer_template=args.analyzer_template,
                generate_summary=not args.no_summary
            )
            
            print(f"🆔 Job ID: {job_id}")
            print("⏳ Waiting for completion...")
            
            # Wait for completion
            final_status = client.wait_for_completion(job_id)
            
            if final_status['status'] == 'completed':
                print(f"✅ Processing completed successfully!")
                
                # Download results
                print("\n⬇️  Downloading results...")
                try:
                    markdown_path = client.download_result(job_id, 'markdown')
                    print(f"📝 Enhanced Markdown: {markdown_path}")
                except Exception as e:
                    print(f"❌ Failed to download markdown: {e}")
                
                if not args.no_summary:
                    try:
                        summary_path = client.download_result(job_id, 'summary')
                        print(f"📊 Summary: {summary_path}")
                    except Exception as e:
                        print(f"❌ Failed to download summary: {e}")
                
                # Show result details
                if 'result' in final_status:
                    result = final_status['result']
                    print(f"\n📈 Processing Results:")
                    print(f"   Status: {result.get('processing_status', 'unknown')}")
                    if 'enhanced_markdown_content' in result:
                        print(f"   Markdown Length: {len(result['enhanced_markdown_content']):,} characters")
                    if 'figures_directory' in result:
                        print(f"   Figures Directory: {result['figures_directory']}")
            
            else:
                print(f"❌ Processing failed: {final_status.get('error', 'Unknown error')}")
        
        else:
            print("\n💡 Usage examples:")
            print(f"   Test pipeline: python {__file__} --test-only")
            print(f"   Process PDF: python {__file__} --pdf-path data/sample.pdf")
            print(f"   List jobs: python {__file__} --list-jobs")
            print(f"   Check job: python {__file__} --job-status JOB_ID")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API server at {args.base_url}")
        print("   Make sure the server is running with: python api_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
