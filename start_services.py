#!/usr/bin/env python3
"""
Startup script for running both services

This script provides easy commands to start:
1. Standalone summarization service (port 8001)
2. Main document processing service (port 8000)  
3. Both services together

Usage:
    python start_services.py summarization    # Start only summarization service
    python start_services.py main            # Start only main service  
    python start_services.py both            # Start both services
    python start_services.py --help          # Show help
"""

import sys
import time
import subprocess
import signal
import requests
from pathlib import Path


def start_summarization_service():
    """Start the standalone summarization service on port 8001"""
    print("🚀 Starting Standalone Book Summarization Service...")
    print("📍 URL: http://localhost:8001")
    print("📖 Docs: http://localhost:8001/docs")
    print("🔍 Health: http://localhost:8001/health")
    print()

    # Run the summarization service
    subprocess.run([sys.executable, "summarization_service.py"])


def start_main_service():
    """Start the main document processing service on port 8000"""
    print("🚀 Starting Main Document Processing Service...")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/enhanced/status")
    print()

    # Run the main service
    subprocess.run([sys.executable, "run_server.py"])


def check_service_health(url, service_name):
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(
                f"⚠️ {service_name} responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} is not responding: {e}")
        return False


def start_both_services():
    """Start both services in parallel"""
    print("🚀 Starting Both Services...")
    print("📍 Summarization Service: http://localhost:8001")
    print("📍 Main Service: http://localhost:8000")
    print()

    # Start summarization service in background
    print("Starting summarization service...")
    summarization_process = subprocess.Popen(
        [sys.executable, "summarization_service.py"])

    # Wait a moment
    time.sleep(3)

    # Start main service in background
    print("Starting main service...")
    main_process = subprocess.Popen([sys.executable, "run_server.py"])

    # Wait for services to start
    print("⏳ Waiting for services to initialize...")
    time.sleep(10)

    # Check health
    print("\n🔍 Health Check:")
    summarization_healthy = check_service_health(
        "http://localhost:8001/health", "Summarization Service")
    main_healthy = check_service_health(
        "http://localhost:8000/docs", "Main Service")

    if summarization_healthy and main_healthy:
        print("\n🎉 Both services are running successfully!")
        print("\n📋 Available Services:")
        print("  • Standalone Summarization: http://localhost:8001/docs")
        print("  • Document Processing: http://localhost:8000/docs")
        print("\n💡 The main service can now call the summarization service automatically!")
    else:
        print("\n⚠️ Some services may not be fully ready yet")

    # Handle shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down services...")
        summarization_process.terminate()
        main_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Wait for both processes
        summarization_process.wait()
        main_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Services stopped")


def show_help():
    """Show usage help"""
    print("""
🔧 Service Management Tool

Commands:
  summarization    Start standalone summarization service (port 8001)
  main            Start main document processing service (port 8000)
  both            Start both services together
  --help          Show this help

Examples:
  python start_services.py summarization
  python start_services.py both

📋 Service Architecture:
  • Standalone Summarization Service (port 8001)
    - Independent book summarization from markdown
    - Can be used by any client via REST API
    
  • Main Document Processing Service (port 8000)  
    - PDF processing with Azure Document Intelligence
    - Content understanding and markdown generation
    - Automatically calls summarization service for book summaries
    
  • Both Services Together
    - Complete end-to-end processing pipeline
    - PDF → Markdown → Book Summary
    - Microservices architecture with automatic failover
""")


def main():
    if len(sys.argv) != 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "summarization":
        start_summarization_service()
    elif command == "main":
        start_main_service()
    elif command == "both":
        start_both_services()
    elif command in ["--help", "-h", "help"]:
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()
