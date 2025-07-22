#!/usr/bin/env python3
"""
Search for year1_return variable in Report_Variables
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
report_variables = base.table('Report_Variables')

def main():
    print("=== SEARCHING FOR YEAR1_RETURN ===")
    variables = report_variables.all()
    
    # Look for year1_return
    found_variables = []
    for var in variables:
        fields = var.get('fields', {})
        variable_id = fields.get('Variable_ID', '')
        if 'year1' in variable_id.lower() or 'return' in variable_id.lower():
            found_variables.append(var)
    
    if found_variables:
        for var in found_variables:
            print(json.dumps(var, indent=2))
    else:
        print("No year1_return variable found. Let me check all Variable_IDs:")
        all_ids = []
        for var in variables:
            fields = var.get('fields', {})
            variable_id = fields.get('Variable_ID', '')
            if variable_id:
                all_ids.append(variable_id)
        
        print(f"All Variable_IDs: {sorted(all_ids)}")

if __name__ == "__main__":
    main()
