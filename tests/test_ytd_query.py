#!/usr/bin/env python3
"""
Test script to debug YTD query issues with Generated_Reports table
"""

import os
import sys
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
GENERATED_REPORTS_TABLE = 'Generated_Reports'

# Initialize Airtable API
if AIRTABLE_API_KEY is None:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set.")
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)

def test_record_details():
    """Test specific record details for the known test case"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    # Test records
    current_record_id = 'reccNSoJ9evk5s0PE'
    expected_match_id = 'recnf7eLeS23IBDVR'
    
    print("=== TESTING SPECIFIC RECORDS ===")
    
    # Get current record details
    try:
        current_record = table.get(current_record_id)
        print(f"\nCurrent record ({current_record_id}):")
        print(f"  client_record_id: {current_record['fields'].get('client_record_id')}")
        print(f"  date_start: {current_record['fields'].get('date_start')}")
        print(f"  date_end: {current_record['fields'].get('date_end')}")
        print(f"  is_full_month: {current_record['fields'].get('is_full_month')}")
        print(f"  month: {current_record['fields'].get('month')}")
        print(f"  year: {current_record['fields'].get('year')}")
    except Exception as e:
        print(f"Error getting current record: {e}")
    
    # Get expected match details
    try:
        match_record = table.get(expected_match_id)
        print(f"\nExpected match ({expected_match_id}):")
        print(f"  client_record_id: {match_record['fields'].get('client_record_id')}")
        print(f"  date_start: {match_record['fields'].get('date_start')}")
        print(f"  date_end: {match_record['fields'].get('date_end')}")
        print(f"  is_full_month: {match_record['fields'].get('is_full_month')}")
        print(f"  month: {match_record['fields'].get('month')}")
        print(f"  year: {match_record['fields'].get('year')}")
    except Exception as e:
        print(f"Error getting expected match: {e}")

def test_current_query_approach():
    """Test the current query approach from the YTD function"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    print("\n=== TESTING CURRENT QUERY APPROACH ===")
    
    # Get all records (current approach)
    try:
        all_records = table.all()
        print(f"Total records in Generated_Reports: {len(all_records)}")
        
        # Look for our test records
        current_found = False
        match_found = False
        
        for record in all_records:
            if record['id'] == 'reccNSoJ9evk5s0PE':
                current_found = True
                print(f"Found current record in all_records query")
            if record['id'] == 'recnf7eLeS23IBDVR':
                match_found = True
                print(f"Found expected match in all_records query")
        
        if not current_found:
            print("ERROR: Current record not found in all_records query")
        if not match_found:
            print("ERROR: Expected match not found in all_records query")
            
    except Exception as e:
        print(f"Error with all_records query: {e}")

def test_lookup_field_matching():
    """Test how lookup field matching works"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    print("\n=== TESTING LOOKUP FIELD MATCHING ===")
    
    try:
        # Get the two specific records
        current_record = table.get('reccNSoJ9evk5s0PE')
        match_record = table.get('recnf7eLeS23IBDVR')
        
        current_client = current_record['fields'].get('client_record_id')
        match_client = match_record['fields'].get('client_record_id')
        
        print(f"Current client_record_id: {current_client} (type: {type(current_client)})")
        print(f"Match client_record_id: {match_client} (type: {type(match_client)})")
        
        # Test various comparison methods
        print(f"Direct comparison: {current_client == match_client}")
        
        if isinstance(current_client, list) and isinstance(match_client, list):
            print(f"List comparison: {current_client[0] == match_client[0] if current_client and match_client else 'One or both are empty'}")
        
        # Test date comparison
        current_date_start = current_record['fields'].get('date_start')
        match_date_end = match_record['fields'].get('date_end')
        
        print(f"Current date_start: {current_date_start} (type: {type(current_date_start)})")
        print(f"Match date_end: {match_date_end} (type: {type(match_date_end)})")
        
    except Exception as e:
        print(f"Error in lookup field matching test: {e}")

def test_filtered_query():
    """Test a filtered query approach"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    print("\n=== TESTING FILTERED QUERY ===")
    
    try:
        # Try a simple filter first
        formula = "AND({is_full_month} = TRUE())"
        filtered_records = table.all(formula=formula)
        print(f"Records with is_full_month = TRUE: {len(filtered_records)}")
        
        # Check if our expected match is in there
        match_found = False
        for record in filtered_records:
            if record['id'] == 'recnf7eLeS23IBDVR':
                match_found = True
                print(f"Expected match found in filtered results")
                break
        
        if not match_found:
            print("Expected match NOT found in filtered results")
            
    except Exception as e:
        print(f"Error with filtered query: {e}")

if __name__ == "__main__":
    print("Starting YTD Query Debug Tests...")
    
    test_record_details()
    test_current_query_approach()
    test_lookup_field_matching()
    test_filtered_query()
    
    print("\n=== TEST COMPLETE ===")
