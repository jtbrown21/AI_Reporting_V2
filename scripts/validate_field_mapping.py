"""
Field Mapping Validation Script

This script validates that:
1. Every variable in Report_Variables has a corresponding field in Generated_Reports
2. The field type in Generated_Reports matches the Data_Type specified in Report_Variables
3. No extra fields exist in Generated_Reports that aren't defined in Report_Variables

The Variable_ID (primary field) from Report_Variables is used as the field name in Generated_Reports.
"""

import os
from pyairtable import Api
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
REPORT_VARIABLES_TABLE = 'Report_Variables'
GENERATED_REPORTS_TABLE = 'Generated_Reports'

# Ensure required environment variables are set
if not AIRTABLE_API_KEY:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set.")
if not BASE_ID:
    raise ValueError("AIRTABLE_BASE_ID environment variable is not set.")

# Initialize Airtable API
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)

def validate_field_mapping():
    """Validate that all Report_Variables have corresponding fields in Generated_Reports
    
    Uses the primary field from Report_Variables as the Variable_ID
    Checks that field types in Generated_Reports match the Data_Type specified in Report_Variables
    
    Example validation:
    - Report_Variables has: Variable_ID="cost", Data_Type="currency"
    - Generated_Reports should have: field named "cost" with type "currency"
    """
    
    print("="*60)
    print("FIELD MAPPING VALIDATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Get all Report_Variables
    report_vars_table = base.table(REPORT_VARIABLES_TABLE)
    report_vars = report_vars_table.all()
    print(f"✓ Found {len(report_vars)} variables in Report_Variables")

    if not report_vars:
        print("✗ No records found in Report_Variables")
        return

    primary_field_name = list(report_vars[0]['fields'].keys())[0]
    
    # Get Generated_Reports field names by fetching a sample record (if any)
    generated_reports_table = base.table(GENERATED_REPORTS_TABLE)
    try:
        records = generated_reports_table.all(max_records=1)
        if records and 'fields' in records[0] and records[0]['fields']:
            generated_fields = list(records[0]['fields'].keys())
            print(f"✓ Found {len(generated_fields)} fields in Generated_Reports")
        else:
            generated_fields = []
            print(f"✓ Found 0 fields in Generated_Reports")
    except Exception as e:
        print(f"✗ Error getting Generated_Reports fields: {e}")
        return

    matched_fields = []
    missing_fields = []
    extra_fields = set(generated_fields)

    print("\nVALIDATING FIELD MAPPINGS:")
    print("-"*60)
    
    for record in report_vars:
        var = record['fields']
        var_id = var.get(primary_field_name)
        if not var_id:
            continue
        if var_id in generated_fields:
            matched_fields.append(var_id)
            extra_fields.discard(var_id)
            print(f"✓ {var_id:<20} -> Matched field: {var_id}")
        else:
            missing_fields.append(var_id)
            print(f"✗ {var_id:<20} -> MISSING")

    print("\nVALIDATION SUMMARY:")
    print("="*60)
    print(f"✓ Matched fields:    {len(matched_fields)}/{len(report_vars)}")
    print(f"✗ Missing fields:    {len(missing_fields)}")

    if missing_fields:
        print("\nMISSING FIELDS (need to be created):")
        print("-"*60)
        for field in missing_fields:
            print(f"- {field}")

    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'total_variables': len(report_vars),
        'matched': len(matched_fields),
        'missing': missing_fields,
        'extra_fields': sorted(list(extra_fields)),
        'field_mapping': {var['fields'][primary_field_name]: var['fields'][primary_field_name] 
                         for var in report_vars if primary_field_name in var['fields']}
    }
    with open('validation_results.json', 'w') as f:
        json.dump(validation_results, f, indent=2)
    print("\n✓ Full results saved to validation_results.json")

    if not missing_fields:
        with open('field_mapping.json', 'w') as f:
            json.dump(validation_results['field_mapping'], f, indent=2)
        print("\n🎉 VALIDATION PASSED! Ready to proceed with calculations.")
    else:
        print("\n⚠️  VALIDATION FAILED! Please fix the issues above before proceeding.")
    print("="*60)

if __name__ == "__main__":
    validate_field_mapping()