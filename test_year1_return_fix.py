#!/usr/bin/env python3
"""
Test the fix for year1_return calculation
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to the path for imports
sys.path.append(str(Path(__file__).parent / 'scripts'))

from calculation_engine import main as run_calculation_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    record_id = 'recZ7bpqcK2Q8lxqR'
    
    print(f"Testing calculation engine fix for record: {record_id}")
    print("=" * 60)
    
    # Run the calculation engine for this specific record
    try:
        result = run_calculation_engine(record_id)
        print(f"\nCalculation completed. Result: {result}")
    except Exception as e:
        print(f"Error running calculation engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
