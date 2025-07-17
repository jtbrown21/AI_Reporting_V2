#!/usr/bin/env python3
"""
Test script to verify single deployment behavior
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "scripts"))

from report_generator import ReportGenerator

def test_single_deploy():
    """Test that report generation creates only one commit"""
    print("Testing single deployment...")
    
    # Create report generator
    generator = ReportGenerator()
    
    # Test record ID
    report_id = "reczkDVKkzx5NuWSV"
    
    print(f"Testing report generation for {report_id}")
    print("This should create ONLY ONE commit to GitHub...")
    
    # Call generate_and_deploy directly (what report-only webhook does)
    url = generator.generate_and_deploy(report_id)
    
    if url:
        print(f"✓ Report generated successfully: {url}")
        print("Check GitHub Actions - should see only ONE workflow run")
    else:
        print("✗ Report generation failed")

if __name__ == "__main__":
    test_single_deploy()
