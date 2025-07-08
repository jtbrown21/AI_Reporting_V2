#!/usr/bin/env python3
"""
Test Report Generator - Local Testing Tool

This script provides a convenient way to test report generation locally
without deploying to GitHub Pages or updating Airtable records.

Features:
- Validates data mapping
- Generates HTML reports in development mode
- Creates validation reports with detailed feedback
- Saves all outputs to templates/development/
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add the scripts directory to the path
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, scripts_dir)

from report_generator import ReportGenerator

def list_development_files():
    """List all files in the development directory"""
    dev_dir = Path(__file__).parent / "templates" / "development"
    if not dev_dir.exists():
        print("Development directory doesn't exist yet.")
        return
    
    files = list(dev_dir.glob("*"))
    if not files:
        print("No files in development directory.")
        return
    
    print(f"\n📁 Files in templates/development/ ({len(files)} files):")
    for file in sorted(files):
        if file.is_file():
            size = file.stat().st_size
            modified = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"  {file.name:<40} {size:>8} bytes  {modified.strftime('%Y-%m-%d %H:%M')}")

def clean_development_directory():
    """Clean the development directory"""
    dev_dir = Path(__file__).parent / "templates" / "development"
    if not dev_dir.exists():
        print("Development directory doesn't exist.")
        return
    
    files = list(dev_dir.glob("*"))
    if not files:
        print("Development directory is already empty.")
        return
    
    for file in files:
        if file.is_file():
            file.unlink()
    
    print(f"✓ Cleaned development directory ({len(files)} files removed)")

def test_report(report_id: str, verbose: bool = False):
    """Test a single report"""
    print(f"🧪 Testing report generation for ID: {report_id}")
    print("=" * 50)
    
    try:
        generator = ReportGenerator(test_mode=True)
        result = generator.generate_test_report(report_id)
        
        if result:
            print(f"\n✅ Test completed successfully!")
            print(f"📊 Validation: {'✓ PASSED' if result['validation_results']['valid'] else '✗ FAILED'}")
            print(f"📄 HTML report: {result['html_file']}")
            print(f"📋 Validation report: {result['validation_file']}")
            
            if verbose and result['validation_results']['field_mappings']:
                print(f"\n📝 Template field mappings:")
                for field, value in result['validation_results']['field_mappings'].items():
                    print(f"  {field}: {value}")
        else:
            print(f"\n❌ Test failed - could not generate report")
            
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()

def batch_test_reports(report_ids: List[str]):
    """Test multiple reports in batch"""
    print(f"🧪 Batch testing {len(report_ids)} reports")
    print("=" * 50)
    
    results = []
    for i, report_id in enumerate(report_ids, 1):
        print(f"\n[{i}/{len(report_ids)}] Testing {report_id}...")
        try:
            generator = ReportGenerator(test_mode=True)
            result = generator.generate_test_report(report_id)
            results.append({
                'report_id': report_id,
                'success': result is not None,
                'valid': result['validation_results']['valid'] if result else False,
                'client_name': result['client_name'] if result else 'Unknown'
            })
        except Exception as e:
            print(f"❌ Error testing {report_id}: {e}")
            results.append({
                'report_id': report_id,
                'success': False,
                'valid': False,
                'client_name': 'Error',
                'error': str(e)
            })
    
    # Summary
    print(f"\n📊 Batch Test Summary:")
    print("=" * 50)
    successful = sum(1 for r in results if r['success'])
    valid = sum(1 for r in results if r['valid'])
    
    print(f"Total reports tested: {len(report_ids)}")
    print(f"Successfully generated: {successful}")
    print(f"Validation passed: {valid}")
    print(f"Failed: {len(report_ids) - successful}")
    
    # Save batch results
    batch_results_file = Path(__file__).parent / "templates" / "development" / f"batch_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(batch_results_file, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_reports': len(report_ids),
            'successful': successful,
            'valid': valid,
            'results': results
        }, f, indent=2)
    
    print(f"📄 Batch results saved to: {batch_results_file}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Test Report Generator - Local Testing Tool")
        print("=" * 45)
        print("")
        print("Usage:")
        print("  python test_report_generator.py <command> [options]")
        print("")
        print("Commands:")
        print("  test <report_id>           Test a single report")
        print("  test <report_id> --verbose Test with detailed output")
        print("  batch <id1> <id2> ...      Test multiple reports")
        print("  list                       List files in development directory")
        print("  clean                      Clean development directory")
        print("")
        print("Examples:")
        print("  python test_report_generator.py test recABC123")
        print("  python test_report_generator.py test recABC123 --verbose")
        print("  python test_report_generator.py batch recABC123 recDEF456 recGHI789")
        print("  python test_report_generator.py list")
        print("  python test_report_generator.py clean")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        if len(sys.argv) < 3:
            print("Error: test command requires a report ID")
            return
        
        report_id = sys.argv[2]
        verbose = "--verbose" in sys.argv
        test_report(report_id, verbose)
        
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Error: batch command requires at least one report ID")
            return
        
        report_ids = sys.argv[2:]
        # Remove any flags from report IDs
        report_ids = [rid for rid in report_ids if not rid.startswith('--')]
        batch_test_reports(report_ids)
        
    elif command == "list":
        list_development_files()
        
    elif command == "clean":
        clean_development_directory()
        
    else:
        print(f"Error: Unknown command '{command}'")
        print("Use 'python test_report_generator.py' for help")

if __name__ == "__main__":
    main()
