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
    print("=== REPORT_VARIABLES CONFIGURATION ===")
    variables = report_variables.all()
    
    # Filter for year1_return
    year1_return_var = None
    for var in variables:
        if var['fields'].get('Variable_Name') == 'year1_return':
            year1_return_var = var
            break
    
    if year1_return_var:
        print(json.dumps(year1_return_var, indent=2))
        
        fields = year1_return_var.get('fields', {})
        print(f"\n=== KEY FIELDS ===")
        print(f"Variable_Name: {fields.get('Variable_Name')}")
        print(f"Data_Type: {fields.get('Data_Type')}")
        print(f"Display_Format: {fields.get('Display_Format')}")
        print(f"Decimal_Places: {fields.get('Decimal_Places')}")
        print(f"Calculation_Level: {fields.get('Calculation_Level')}")
        print(f"Formula: {fields.get('Formula')}")
    else:
        print("year1_return variable not found in Report_Variables")
    
    # Also look for other percentage type variables for comparison
    print(f"\n=== ALL PERCENTAGE TYPE VARIABLES ===")
    percentage_vars = []
    for var in variables:
        if var['fields'].get('Data_Type') == 'percentage':
            var_name = var['fields'].get('Variable_Name')
            decimal_places = var['fields'].get('Decimal_Places', 'not set')
            percentage_vars.append((var_name, decimal_places))
    
    for var_name, decimal_places in percentage_vars:
        print(f"- {var_name}: {decimal_places} decimal places")

if __name__ == "__main__":
    main()
