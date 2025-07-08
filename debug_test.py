#!/usr/bin/env python3
"""
Simple test to see if we can load the report_generator module without dependencies
"""

import sys
import os
from pathlib import Path

# Add the scripts directory to the path
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, scripts_dir)

try:
    print("Testing basic Python imports...")
    import json
    import datetime
    print("✅ Basic imports work")
    
    print("\nTesting report_generator import...")
    # Let's see what line causes the issue
    try:
        import report_generator
        print("✅ report_generator imported successfully")
    except Exception as e:
        print(f"❌ Error importing report_generator: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error in basic imports: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("Environment Info:")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
