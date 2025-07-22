#!/usr/bin/env python3
"""
Debug script to investigate year1_return value for record recZ7bpqcK2Q8lxqR
"""

import os
import sys
from pyairtable import Api
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')

# Initialize Airtable API
if AIRTABLE_API_KEY is None:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set.")
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)

# Tables
generated_reports = base.table('Generated_Reports')
report_variables = base.table('Report_Variables')

def main():
    record_id = 'recZ7bpqcK2Q8lxqR'
    
    try:
        # Fetch the record from Generated_Reports
        print(f"Fetching record {record_id} from Generated_Reports...")
        record = generated_reports.get(record_id)
        
        print("\n=== RAW RECORD ===")
        print(json.dumps(record, indent=2))
        
        # Extract year1_return value
        fields = record.get('fields', {})
        year1_return_value = fields.get('year1_return')
        
        print(f"\n=== YEAR1_RETURN VALUE ===")
        print(f"Raw value: {year1_return_value}")
        print(f"Type: {type(year1_return_value)}")
        
        # Also check the Report_Variables config
        print(f"\n=== REPORT_VARIABLES CONFIG ===")
        variables = report_variables.all()
        for var in variables:
            if var['fields'].get('Variable_Name') == 'year1_return':
                print(json.dumps(var, indent=2))
                break
        
        # Calculate what the displayed value should be
        if year1_return_value is not None:
            if isinstance(year1_return_value, (int, float)):
                # Apply percentage formatting (multiply by 100)
                formatted_value = year1_return_value * 100
                print(f"\n=== CALCULATION ===")
                print(f"Raw value: {year1_return_value}")
                print(f"Formatted as percentage: {formatted_value}%")
                print(f"Expected display (if 166%): {formatted_value:.0f}%")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
