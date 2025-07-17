#!/usr/bin/env python3
"""
Test currency parsing fix
"""

import sys
sys.path.append('scripts')

from calculation_engine import validate_value, check_expected_range, parse_numeric_value

def test_currency_parsing():
    print("Testing currency parsing fixes...")
    
    # Test the parse_numeric_value function
    print("\n1. Testing parse_numeric_value function:")
    test_values = [
        "2,500",
        "$2,500",
        "2500",
        "2,500.50",
        "$2,500.50",
        "10%",
        "5.5%",
        "1000",
        1000,
        1000.5
    ]
    
    for val in test_values:
        try:
            result = parse_numeric_value(val)
            print(f"   '{val}' -> {result}")
        except Exception as e:
            print(f"   '{val}' -> ERROR: {e}")
    
    # Test validation with currency values
    print("\n2. Testing validation with currency values:")
    test_cases = [
        ("2,500", ">= 1000 AND <= 5000", "Currency with comma"),
        ("$2,500", ">= 1000 AND <= 5000", "Currency with dollar sign and comma"),
        ("10%", ">= 0 AND <= 1", "Percentage value"),
        ("500", ">= 1000 AND <= 5000", "Plain number that should fail")
    ]
    
    for value, rule, description in test_cases:
        is_valid, msg = validate_value(value, rule)
        print(f"   {description}: '{value}' with rule '{rule}'")
        print(f"     Valid: {is_valid}, Message: '{msg}'")
    
    # Test expected range with currency
    print("\n3. Testing expected range with currency values:")
    test_cases = [
        ("2,500", ">= 2000 AND <= 3000", "Currency in range"),
        ("$1,500", ">= 2000 AND <= 3000", "Currency out of range")
    ]
    
    for value, rule, description in test_cases:
        is_in_range, msg = check_expected_range(value, rule)
        print(f"   {description}: '{value}' with rule '{rule}'")
        print(f"     In Range: {is_in_range}, Message: '{msg}'")
    
    print("\n✅ Currency parsing test completed!")

if __name__ == "__main__":
    test_currency_parsing()
