#!/usr/bin/env python3
"""
Test report generation with the fixed year1_return value
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to the path for imports
sys.path.append(str(Path(__file__).parent / 'scripts'))

from report_generator import ReportGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    record_id = 'recZ7bpqcK2Q8lxqR'
    
    print(f"Testing report generation for record: {record_id}")
    print("=" * 60)
    
    # Generate the report
    try:
        generator = ReportGenerator()
        result = generator.generate_and_deploy(record_id)
        
        if result:
            print(f"\n✅ Report generated and deployed successfully!")
            print(f"Report URL: {result}")
        else:
            print(f"\n❌ Report generation failed")
            
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
