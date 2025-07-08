#!/usr/bin/env python3
"""
Quick Start Script for Report Generation System

This script helps you get started with the report generation system.
"""

import os
import sys
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_environment_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        return True
    
    template_file = Path(".env.template")
    if template_file.exists():
        print("? .env file not found, but template exists")
        response = input("Copy .env.template to .env? (y/n): ").lower()
        if response == 'y':
            shutil.copy(template_file, env_file)
            print("✓ Created .env file from template")
            print("⚠ Please edit .env file with your actual values")
            return True
    
    print("✗ .env file not found")
    return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✓ Dependencies installed")

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ python-dotenv imported successfully")
        
        from pyairtable import Api
        print("✓ pyairtable imported successfully")
        
        import pandas as pd
        print("✓ pandas imported successfully")
        
        try:
            from flask import Flask
            print("✓ flask imported successfully")
        except ImportError:
            print("⚠ flask not found (needed for webhook server)")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID',
        'GITHUB_TOKEN',
        'GITHUB_REPO',
        'WEBHOOK_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.environ.get(var) and os.environ.get(var) != f"your-{var.lower().replace('_', '-')}":
            print(f"✓ {var} is set")
        else:
            missing_vars.append(var)
            print(f"✗ {var} is not set or using placeholder value")
    
    if missing_vars:
        print(f"\n⚠ Please set these variables in your .env file:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        # Test Airtable connection
        from dotenv import load_dotenv
        load_dotenv()
        
        from pyairtable import Api
        api_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        
        if api_key and base_id:
            api = Api(api_key)
            base = api.base(base_id)
            print("✓ Airtable connection test passed")
        else:
            print("✗ Airtable connection test failed (missing credentials)")
            return False
        
        # Test report generator import
        sys.path.append(str(Path(__file__).parent / "scripts"))
        from report_generator import ReportGenerator
        print("✓ Report generator import test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("="*60)
    print("REPORT GENERATION SYSTEM - QUICK START")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check environment file
    if not check_environment_file():
        print("\n⚠ Please create .env file with your configuration")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Test imports
    if not test_imports():
        print("\n⚠ Some dependencies are missing. Please install them.")
        sys.exit(1)
    
    # Check environment variables
    if not check_environment_variables():
        print("\n⚠ Please set the required environment variables in your .env file")
        sys.exit(1)
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n⚠ Basic functionality test failed. Please check your configuration.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Set up GitHub repository and Pages (see GITHUB_PAGES_SETUP.md)")
    print("2. Deploy to Railway (see REPORT_GENERATION_SYSTEM.md)")
    print("3. Configure n8n workflow (see N8N_WORKFLOW_TEMPLATE.md)")
    print("4. Test the system:")
    print("   - python scripts/report_generator.py recABC123")
    print("   - python scripts/webhook_server.py")
    print("   - python test/test_report_generation.py")
    print("\nDocumentation:")
    print("- REPORT_GENERATION_SYSTEM.md - Complete documentation")
    print("- GITHUB_PAGES_SETUP.md - GitHub Pages setup guide")
    print("- N8N_WORKFLOW_TEMPLATE.md - n8n workflow template")

if __name__ == "__main__":
    main()
