#!/usr/bin/env python3
"""
Example script demonstrating test mode usage
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to the path
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, scripts_dir)

# Import the ReportGenerator
try:
    from report_generator import ReportGenerator
    print("✓ Successfully imported ReportGenerator")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_example():
    """Example of using test mode programmatically"""
    print("🧪 Test Mode Example")
    print("=" * 30)
    
    # Example report ID - you would replace this with a real one
    test_report_id = "recABC123"
    
    try:
        # Create generator in test mode
        generator = ReportGenerator(test_mode=True)
        print(f"✓ ReportGenerator created in test mode")
        
        # Generate test report
        print(f"Testing report ID: {test_report_id}")
        result = generator.generate_test_report(test_report_id)
        
        if result:
            print(f"\n✅ Test completed!")
            print(f"HTML file: {result['html_file']}")
            print(f"Validation file: {result['validation_file']}")
            print(f"Client: {result['client_name']}")
            print(f"Valid: {result['validation_results']['valid']}")
        else:
            print(f"\n❌ Test failed")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Environment Check")
    print("=" * 20)
    
    required_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var}: {'*' * min(len(value), 10)}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check if development directory exists
    dev_dir = Path(__file__).parent / "templates" / "development"
    if dev_dir.exists():
        print(f"✓ Development directory exists: {dev_dir}")
    else:
        print(f"❌ Development directory missing: {dev_dir}")

if __name__ == "__main__":
    print("Report Generator Test Mode Example")
    print("=" * 40)
    
    check_environment()
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_example()
    else:
        print("Usage:")
        print("  python example_test_mode.py test")
        print()
        print("Or use the dedicated test script:")
        print("  python test_report_generator.py test <report_id>")
