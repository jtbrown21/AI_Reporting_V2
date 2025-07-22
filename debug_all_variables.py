#!/usr/bin/env python3
"""
Debug script to check Report_Variables configuration
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
    print("=== ALL REPORT_VARIABLES ===")
    variables = report_variables.all()
    
    # Show first few variables to understand structure
    for i, var in enumerate(variables[:5]):
        print(f"\n--- Variable {i+1} ---")
        print(json.dumps(var, indent=2))
    
    # Look for year1_return by name
    year1_return_vars = []
    for var in variables:
        fields = var.get('fields', {})
        variable_name = fields.get('Variable_Name')
        if variable_name and 'year1' in variable_name.lower():
            year1_return_vars.append(var)
    
    print(f"\n=== YEAR1_RETURN MATCHES ===")
    for var in year1_return_vars:
        print(json.dumps(var, indent=2))

if __name__ == "__main__":
    main()
