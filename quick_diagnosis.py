#!/usr/bin/env python3
"""
Quick RAG System Diagnosis & Fix
================================

Fast diagnosis and repair script for the RAG system startup issues.
"""

import subprocess
import time
import requests
from pathlib import Path
import os

def check_port(port):
    """Quick port check using netstat"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"',
            shell=True, capture_output=True, text=True, timeout=5
        )
        return port in result.stdout
    except:
        return False

def quick_service_check():
    """Quick check of all services"""
    services = {
        'Ollama (11434)': check_port(11434),
        'AI Service (8001)': check_port(8001),
        'App Server (3001)': check_port(3001),
        'React Client (3000)': check_port(3000)
    }
    
    print("=== Quick Service Status ===")
    for service, status in services.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'Running' if status else 'Not Running'}")
    
    return services

def test_ai_service_direct():
    """Test AI Service directly if it's running"""
    if check_port(8001):
        try:
            response = requests.get('http://localhost:8001/api/status', timeout=5)
            print(f"✅ AI Service responds: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ AI Service error: {str(e)[:100]}")
            return False
    else:
        print("❌ AI Service not running on port 8001")
        return False

def manual_start_ai_service():
    """Manually start AI Service"""
    print("\n=== Manually Starting AI Service ===")
    
    # Check if virtual environment exists
    venv_path = Path("ai-service/venv/Scripts/activate")
    if not venv_path.exists():
        print("❌ Virtual environment not found at ai-service/venv/")
        return False
    
    # Start AI Service
    try:
        cmd = 'cd ai-service && .\\venv\\Scripts\\activate && uvicorn main:app --host 0.0.0.0 --port 8001'
        print(f"Starting: {cmd}")
        
        # Use Popen for non-blocking start
        process = subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print("✅ AI Service start command executed")
        print(f"Process ID: {process.pid}")
        
        # Wait a moment and check if port is active
        time.sleep(3)
        if check_port(8001):
            print("✅ AI Service is now running on port 8001")
            return True
        else:
            print("⚠️ AI Service may still be starting...")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start AI Service: {e}")
        return False

def manual_start_app_server():
    """Manually start App Server"""
    print("\n=== Manually Starting App Server ===")
    
    # Check if package.json exists
    package_path = Path("app-server/package.json")
    if not package_path.exists():
        print("❌ package.json not found in app-server/")
        return False
    
    try:
        cmd = 'cd app-server && npm start'
        print(f"Starting: {cmd}")
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print("✅ App Server start command executed")
        print(f"Process ID: {process.pid}")
        
        time.sleep(3)
        if check_port(3001):
            print("✅ App Server is now running on port 3001")
            return True
        else:
            print("⚠️ App Server may still be starting...")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start App Server: {e}")
        return False

def manual_start_react_client():
    """Manually start React Client"""
    print("\n=== Manually Starting React Client ===")
    
    # Check if package.json exists
    package_path = Path("client/package.json")
    if not package_path.exists():
        print("❌ package.json not found in client/")
        return False
    
    try:
        cmd = 'cd client && npm start'
        print(f"Starting: {cmd}")
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print("✅ React Client start command executed")
        print(f"Process ID: {process.pid}")
        
        time.sleep(3)
        if check_port(3000):
            print("✅ React Client is now running on port 3000")
            return True
        else:
            print("⚠️ React Client may still be starting...")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start React Client: {e}")
        return False

def test_rag_functionality():
    """Quick test of RAG functionality"""
    print("\n=== Testing RAG Functionality ===")
    
    if not check_port(8001):
        print("❌ AI Service not running, cannot test RAG")
        return False
    
    try:
        # Test simple query
        payload = {
            'query': 'Hello, can you help me?',
            'max_tokens': 50
        }
        
        response = requests.post(
            'http://localhost:8001/api/query',
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAG query successful!")
            print(f"Response: {str(result)[:200]}...")
            return True
        else:
            print(f"❌ RAG query failed: HTTP {response.status_code}")
            print(f"Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ RAG test error: {str(e)[:100]}")
        return False

def main():
    """Main diagnosis and fix routine"""
    print("RAG System Quick Diagnosis & Fix")
    print("=" * 40)
    
    # Step 1: Check current status
    services = quick_service_check()
    
    # Step 2: Test AI Service if running
    if services['AI Service (8001)']:
        ai_working = test_ai_service_direct()
        if ai_working:
            print("✅ AI Service is working properly")
            # Test RAG functionality
            test_rag_functionality()
            return
    
    # Step 3: Manual startup if services are missing
    missing_services = [name for name, status in services.items() if not status]
    
    if missing_services:
        print(f"\n⚠️ Missing services: {', '.join(missing_services)}")
        print("Attempting manual startup...")
        
        # Start AI Service first (most critical)
        if not services['AI Service (8001)']:
            manual_start_ai_service()
            time.sleep(2)
        
        # Start App Server
        if not services['App Server (3001)']:
            manual_start_app_server()
            time.sleep(2)
        
        # Start React Client
        if not services['React Client (3000)']:
            manual_start_react_client()
            time.sleep(2)
        
        # Final check
        print("\n=== Final Status Check ===")
        final_services = quick_service_check()
        
        # Test RAG if AI Service is now running
        if final_services['AI Service (8001)']:
            time.sleep(3)  # Give it a moment to fully start
            test_rag_functionality()
    
    print("\n=== Diagnosis Complete ===")
    print("Check the new console windows for any error messages.")
    print("If services are still not working, check:")
    print("1. Virtual environment in ai-service/venv/")
    print("2. Node.js dependencies in app-server/ and client/")
    print("3. Python dependencies in ai-service/")

if __name__ == "__main__":
    main()
