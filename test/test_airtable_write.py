#!/usr/bin/env python3
"""
Test script to check if average_premium_per_household is being written to Airtable
"""

import os
import sys
from pyairtable import Api

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Configuration
BASE_ID = "appZEEqSgLqGtbHgd"
GENERATED_REPORTS_TABLE = "Generated_Reports"
REPORT_DATABASE_TABLE = "Client_Reports"

# Initialize Airtable
api = Api(os.environ.get('AIRTABLE_API_KEY'))
base = api.base(BASE_ID)

def test_record_field():
    """Test if average_premium_per_household exists in the record"""
    # The record that we've been working with
    record_id = "recgP7kCGtvivnO4q"
    
    # First, check if this record exists in Client_Reports
    try:
        client_table = base.table(REPORT_DATABASE_TABLE)
        record = client_table.get(record_id)
        print(f"✓ Found record in {REPORT_DATABASE_TABLE}")
        print(f"  Record ID: {record['id']}")
        print(f"  Fields: {list(record['fields'].keys())}")
        
        # Check if average_premium_per_household exists
        if 'average_premium_per_household' in record['fields']:
            print(f"  ✓ average_premium_per_household: {record['fields']['average_premium_per_household']}")
        else:
            print(f"  ✗ average_premium_per_household: NOT FOUND")
        
    except Exception as e:
        print(f"✗ Error accessing {REPORT_DATABASE_TABLE}: {e}")
    
    # Now check if there's a corresponding record in Generated_Reports
    try:
        gen_table = base.table(GENERATED_REPORTS_TABLE)
        # Search for records linked to this client report
        matching_records = gen_table.all(
            formula=f"{{client_report}} = '{record_id}'"
        )
        
        if matching_records:
            for gen_record in matching_records:
                print(f"\n✓ Found linked record in {GENERATED_REPORTS_TABLE}")
                print(f"  Record ID: {gen_record['id']}")
                print(f"  Fields: {list(gen_record['fields'].keys())}")
                
                # Check if average_premium_per_household exists
                if 'average_premium_per_household' in gen_record['fields']:
                    print(f"  ✓ average_premium_per_household: {gen_record['fields']['average_premium_per_household']}")
                else:
                    print(f"  ✗ average_premium_per_household: NOT FOUND")
        else:
            print(f"\n✗ No linked records found in {GENERATED_REPORTS_TABLE}")
    
    except Exception as e:
        print(f"✗ Error accessing {GENERATED_REPORTS_TABLE}: {e}")

if __name__ == "__main__":
    test_record_field()
