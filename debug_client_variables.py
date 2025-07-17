#!/usr/bin/env python3
"""
Debug script to check Client_Variables table structure
"""
import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')

def debug_client_variables():
    """Debug the Client_Variables table"""
    airtable = Api(AIRTABLE_API_KEY)
    table = airtable.table(BASE_ID, 'Client_Variables')
    
    # Get first 5 records to inspect structure
    records = table.all(max_records=5)
    
    print(f"Found {len(records)} records in Client_Variables table")
    print("\n" + "="*50)
    
    for i, record in enumerate(records):
        print(f"\nRecord {i+1}:")
        print(f"ID: {record['id']}")
        print(f"Fields available:")
        
        fields = record.get('fields', {})
        for field_name, field_value in fields.items():
            # Show field name and type/length of value
            if isinstance(field_value, str):
                value_info = f"'{field_value[:50]}...'" if len(field_value) > 50 else f"'{field_value}'"
            elif isinstance(field_value, list):
                value_info = f"[list with {len(field_value)} items]"
            else:
                value_info = str(field_value)
            
            print(f"  - {field_name}: {value_info}")
    
    # Test the formula
    print("\n" + "="*50)
    print("Testing formula filter...")
    
    try:
        formula = '{Status (from Active Subscriptions)} != "canceled"'
        filtered_records = table.all(formula=formula, max_records=10)
        print(f"Formula '{formula}' returned {len(filtered_records)} records")
        
        if filtered_records:
            print("Sample filtered record fields:")
            for field_name in filtered_records[0].get('fields', {}).keys():
                print(f"  - {field_name}")
    except Exception as e:
        print(f"Formula test failed: {e}")
        
    # Check for headshot fields
    print("\n" + "="*50)
    print("Looking for headshot-related fields...")
    
    all_fields = set()
    for record in records:
        all_fields.update(record.get('fields', {}).keys())
    
    headshot_fields = [f for f in all_fields if 'headshot' in f.lower() or 'image' in f.lower() or 'photo' in f.lower()]
    print(f"Potential headshot fields: {headshot_fields}")
    
    # Show all field names
    print(f"\nAll available fields ({len(all_fields)}):")
    for field in sorted(all_fields):
        print(f"  - {field}")

if __name__ == "__main__":
    debug_client_variables()
