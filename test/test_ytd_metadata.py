#!/usr/bin/env python3
"""
Test script to show what hhs_ytd_metadata will contain
"""

import json

def test_ytd_metadata():
    print("Testing simplified hhs_ytd_metadata content...")
    
    # Scenario 1: January report (no previous months)
    print("\n1. January Report - hhs_ytd_metadata:")
    metadata_jan = {
        'reason': 'No previous months in current year',
        'months': {},
        'ytd_value': 0
    }
    print(json.dumps(metadata_jan, indent=2))
    
    # Scenario 2: July report with all previous months
    print("\n2. July Report (Complete Data) - hhs_ytd_metadata:")
    metadata_july_complete = {
        'months': {
            '1': 120,
            '2': 110,
            '3': 130,
            '4': 140,
            '5': 125,
            '6': 135
        },
        'ytd_value': 760
    }
    print(json.dumps(metadata_july_complete, indent=2))
    
    # Scenario 3: July report with missing months
    print("\n3. July Report (Missing Data) - hhs_ytd_metadata:")
    metadata_july_partial = {
        'months': {
            '1': 120,
            '2': 'missing',
            '3': 130,
            '4': 140,
            '5': 'missing',
            '6': 135
        },
        'ytd_value': 525
    }
    print(json.dumps(metadata_july_partial, indent=2))
    
    # Scenario 4: July report with no data available
    print("\n4. July Report (No Data Available) - hhs_ytd_metadata:")
    metadata_july_no_data = {
        'reason': 'No complete previous months with data',
        'months': {
            '1': 'missing',
            '2': 'missing',
            '3': 'missing',
            '4': 'missing',
            '5': 'missing',
            '6': 'missing'
        },
        'ytd_value': 0
    }
    print(json.dumps(metadata_july_no_data, indent=2))
    
    print("\nThis simplified metadata will be stored in the hhs_ytd_metadata field in Airtable.")
    print("You can easily see each month's value or if it's missing, plus the total YTD value.")

if __name__ == "__main__":
    test_ytd_metadata()
