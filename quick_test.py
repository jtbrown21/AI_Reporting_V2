#!/usr/bin/env python3
"""
Quick Test Script for Report Generation

This script provides a simple way to test the report generation system
with basic validation and error handling.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup the environment for testing"""
    # Add scripts directory to path
    scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
    sys.path.insert(0, scripts_dir)
    
    # Check environment variables
    required_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return False
    
    return True

def quick_test(report_id: str):
    """Quick test of a single report"""
    print(f"🚀 Quick Test for Report ID: {report_id}")
    print("=" * 40)
    
    if not setup_environment():
        return False
    
    try:
        from report_generator import ReportGenerator
        
        # Create generator in test mode
        generator = ReportGenerator(test_mode=True)
        
        # Run test
        result = generator.generate_test_report(report_id)
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"Client: {result['client_name']}")
            print(f"Valid: {'✓' if result['validation_results']['valid'] else '✗'}")
            print(f"HTML: {result['html_file']}")
            print(f"Validation: {result['validation_file']}")
            
            # Quick validation summary
            validation = result['validation_results']
            if validation['errors']:
                print(f"\n❌ Errors ({len(validation['errors'])}):")
                for error in validation['errors'][:3]:  # Show first 3
                    print(f"  • {error}")
            
            if validation['warnings']:
                print(f"\n⚠️  Warnings ({len(validation['warnings'])}):")
                for warning in validation['warnings'][:3]:  # Show first 3
                    print(f"  • {warning}")
            
            return True
        else:
            print(f"\n❌ FAILED - Could not generate report")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Quick Test Script for Report Generation")
        print("=" * 40)
        print("")
        print("Usage: python quick_test.py <report_id>")
        print("")
        print("Example: python quick_test.py recABC123")
        print("")
        print("This script will:")
        print("• Test report generation in safe mode")
        print("• Validate data mapping")
        print("• Save output to templates/development/")
        print("• Show quick validation summary")
        return
    
    report_id = sys.argv[1]
    success = quick_test(report_id)
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"Check templates/development/ for output files")
    else:
        print(f"\n💔 Test failed. Check error messages above.")

if __name__ == "__main__":
    main()
