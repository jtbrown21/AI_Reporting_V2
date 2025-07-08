"""
Enhanced Calculation Engine with Automatic Report Generation

This script extends the original calculation engine to automatically generate
and deploy HTML reports after successful calculations.
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.append(str(Path(__file__).parent))

from typing import Optional

from calculation_engine import main as original_main
from report_generator import ReportGenerator


def enhanced_main(report_database_id: Optional[str] = None, auto_deploy: bool = True):
    """
    Enhanced main function that runs calculations and optionally generates reports
    
    Args:
        report_database_id: ID of the report to process
        auto_deploy: Whether to automatically generate and deploy HTML report
    """
    print("="*70)
    print("ENHANCED CALCULATION ENGINE WITH REPORT GENERATION")
    print("="*70)
    
    # Run original calculation engine
    print("\nStep 1: Running calculation engine...")
    original_main(report_database_id)
    
    # If auto_deploy is enabled, generate and deploy report
    if auto_deploy:
        print("\nStep 2: Generating and deploying HTML report...")
        try:
            generator = ReportGenerator()
            
            # If no specific report ID provided, we need to find the most recent one
            if not report_database_id:
                print("No report ID provided, this feature requires a specific report ID")
                return
            
            # Generate and deploy report
            url = generator.generate_and_deploy(report_database_id)
            
            if url:
                print(f"\n✓ Report generated and deployed successfully!")
                print(f"🌐 Report URL: {url}")
                print("\nNext steps:")
                print("1. The report is now live on GitHub Pages")
                print("2. The Airtable record has been updated with the GitHub URL")
                print("3. You can share the URL with your client")
            else:
                print("\n✗ Report generation failed")
                print("Check the logs above for error details")
                
        except Exception as e:
            print(f"\n✗ Error during report generation: {e}")
            print("The calculations completed successfully, but report generation failed")
    
    print("\n" + "="*70)
    print("PROCESS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced calculation engine with report generation")
    parser.add_argument("report_id", nargs="?", help="Report ID to process")
    parser.add_argument("--no-deploy", action="store_true", help="Skip report generation and deployment")
    
    args = parser.parse_args()
    
    auto_deploy = not args.no_deploy
    enhanced_main(args.report_id, auto_deploy)
