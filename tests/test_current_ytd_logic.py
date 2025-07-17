#!/usr/bin/env python3
"""
Test the current YTD calculation logic specifically
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

def extract_lookup_value(field):
    """Current function from calculation_engine.py"""
    if isinstance(field, list):
        return field[0] if field else None
    return field

def test_current_ytd_logic():
    """Test the current YTD matching logic"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    print("=== TESTING CURRENT YTD LOGIC ===")
    
    # Simulate the current report context
    current_record = table.get('reccNSoJ9evk5s0PE')
    fields = current_record['fields']
    
    # Extract current report details (as the current code would)
    client_record_id = extract_lookup_value(fields.get('client_record_id'))
    date_start = extract_lookup_value(fields.get('date_start'))
    current_month = extract_lookup_value(fields.get('month'))
    current_year = extract_lookup_value(fields.get('year'))
    
    print(f"Current report details:")
    print(f"  client_record_id: {client_record_id}")
    print(f"  date_start: {date_start}")
    print(f"  current_month: {current_month}")
    print(f"  current_year: {current_year}")
    
    # Get all records and try to match (current approach)
    all_records = table.all()
    
    print(f"\nLooking for YTD matches in {len(all_records)} records...")
    
    # Month name to number mapping (from current code)
    month_names = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    current_month_number = month_names.get(str(current_month) if current_month else "", 0)
    print(f"Current month number: {current_month_number}")
    
    matches = []
    for record in all_records:
        try:
            record_fields = record['fields']
            
            # Extract record details
            record_client_id = extract_lookup_value(record_fields.get('client_record_id'))
            record_is_full_month = extract_lookup_value(record_fields.get('is_full_month'))
            record_month = extract_lookup_value(record_fields.get('month'))
            record_year = extract_lookup_value(record_fields.get('year'))
            record_date_end = extract_lookup_value(record_fields.get('date_end'))
            
            # Check matching conditions
            client_matches = record_client_id == client_record_id
            is_full_month = record_is_full_month == True
            same_year = record_year == current_year
            
            record_month_number = month_names.get(str(record_month) if record_month else "", 0)
            is_earlier_month = record_month_number < current_month_number
            
            # Date comparison
            date_comparison = "N/A"
            if record_date_end and date_start:
                try:
                    record_date_end_parsed = datetime.strptime(record_date_end, "%Y-%m-%d")
                    current_date_start_parsed = datetime.strptime(date_start, "%Y-%m-%d")
                    date_comparison = record_date_end_parsed < current_date_start_parsed
                except Exception as e:
                    date_comparison = f"Error: {e}"
            
            print(f"\nRecord {record['id']}:")
            print(f"  client_id: {record_client_id} (matches: {client_matches})")
            print(f"  is_full_month: {record_is_full_month} (valid: {is_full_month})")
            print(f"  month: {record_month} ({record_month_number}) (earlier: {is_earlier_month})")
            print(f"  year: {record_year} (same: {same_year})")
            print(f"  date_end: {record_date_end} (before start: {date_comparison})")
            
            # Check if this should be a match
            if client_matches and is_full_month and same_year and is_earlier_month:
                matches.append({
                    'id': record['id'],
                    'month': record_month,
                    'month_number': record_month_number,
                    'date_end': record_date_end
                })
                print(f"  *** MATCH FOUND ***")
            
        except Exception as e:
            print(f"Error processing record {record['id']}: {e}")
    
    print(f"\nTotal matches found: {len(matches)}")
    for match in matches:
        print(f"  - {match['id']}: {match['month']} ({match['month_number']})")

if __name__ == "__main__":
    test_current_ytd_logic()
