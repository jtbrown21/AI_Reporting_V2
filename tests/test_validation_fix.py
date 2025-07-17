#!/usr/bin/env python3
"""
Test script to verify the validation fixes work correctly
"""

import sys
sys.path.append('scripts')

from calculation_engine import validate_value, check_expected_range, CalculationContext

def test_validation_fixes():
    print("Testing validation fixes...")
    
    # Test 1: String value that should be converted to float
    print("\n1. Testing string value conversion:")
    is_valid, msg = validate_value("5.5", ">= 0 AND <= 10")
    print(f"   validate_value('5.5', '>= 0 AND <= 10') = {is_valid}, '{msg}'")
    
    # Test 2: Integer validation
    print("\n2. Testing integer validation:")
    is_valid, msg = validate_value(37.094, "integer")
    print(f"   validate_value(37.094, 'integer') = {is_valid}, '{msg}'")
    
    # Test 3: Expected range check with string
    print("\n3. Testing expected range with string:")
    is_in_range, msg = check_expected_range("2.5", ">= 1 AND <= 5")
    print(f"   check_expected_range('2.5', '>= 1 AND <= 5') = {is_in_range}, '{msg}'")
    
    # Test 4: Test validation context with variable names
    print("\n4. Testing validation context:")
    context = CalculationContext()
    context.calculated_values = {
        'fire_per_hh': '0.8',  # String value
        'potential_leads': 37.094,  # Non-integer
        'test_var': 150.0  # Out of range
    }
    
    # Mock report variables
    report_variables = {
        'fire_per_hh': {
            'fields': {
                'Validation_Rules': '>= 0 AND <= 2'
            }
        },
        'potential_leads': {
            'fields': {
                'Validation_Rules': 'integer'
            }
        },
        'test_var': {
            'fields': {
                'Expected_Values': '>= 20 AND <= 60'
            }
        }
    }
    
    # Import and test the validation function
    from calculation_engine import validate_and_flag_results
    validate_and_flag_results(context, report_variables)
    
    print("\n   Validation errors:")
    for error in context.errors:
        print(f"     {error}")
    
    print("\n   Validation warnings:")
    for warning in context.warnings:
        print(f"     {warning}")
    
    print("\n✅ Validation fixes test completed!")

if __name__ == "__main__":
    test_validation_fixes()
