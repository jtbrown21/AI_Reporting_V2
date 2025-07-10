#!/usr/bin/env python3
"""
Test script to verify the percentage conversion tracking solution
"""

import sys
import os

# Ensure the scripts directory is in sys.path before importing calculation_engine
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from calculation_engine import ConversionTracker, safe_percentage_conversion

def test_percentage_conversion():
    """Test that percentages are converted exactly once"""
    
    # Test 1: String percentage converts once
    tracker = ConversionTracker()
    result, converted = safe_percentage_conversion("25%", "test_var", "test_stage", tracker)
    assert result == 0.25, f"Expected 0.25, got {result}"
    assert converted == True, "Should have been converted"
    assert tracker.is_converted("test_var"), "Should be marked as converted"
    
    # Test 2: Already converted value stays the same
    result2, converted2 = safe_percentage_conversion(0.25, "test_var", "test_stage2", tracker)
    assert result2 == 0.25, f"Expected 0.25, got {result2}"
    assert converted2 == False, "Should not convert again"
    
    # Test 3: Whole number percentage converts once
    tracker2 = ConversionTracker()
    result3, converted3 = safe_percentage_conversion(25, "test_var2", "test_stage", tracker2)
    assert result3 == 0.25, f"Expected 0.25, got {result3}"
    assert converted3 == True, "Should have been converted"
    
    # Test 4: Decimal percentage doesn't convert
    tracker3 = ConversionTracker()
    result4, converted4 = safe_percentage_conversion(0.15, "test_var3", "test_stage", tracker3)
    assert result4 == 0.15, f"Expected 0.15, got {result4}"
    assert converted4 == False, "Should not convert decimal"
    
    print("✓ All percentage conversion tests passed")

def test_edge_cases():
    """Test edge cases in percentage conversion"""
    
    # Test 1: Value of exactly 1 (should convert to 0.01)
    tracker = ConversionTracker()
    result, converted = safe_percentage_conversion(1, "test_edge1", "test", tracker)
    assert result == 0.01, f"Expected 0.01 (1%), got {result}"
    assert converted == True, "Should convert 1 to 0.01"
    
    # Test 2: Value of 1.5 (should be 1.5% = 0.015)
    tracker2 = ConversionTracker()
    result2, converted2 = safe_percentage_conversion(1.5, "test_edge2", "test", tracker2)
    assert result2 == 0.015, f"Expected 0.015 (1.5%), got {result2}"
    assert converted2 == True, "Should convert 1.5 to 0.015"
    
    # Test 3: Value of 150 (should be 150% = 1.5)
    tracker3 = ConversionTracker()
    result3, converted3 = safe_percentage_conversion(150, "test_edge3", "test", tracker3)
    assert result3 == 1.5, f"Expected 1.5 (150%), got {result3}"
    assert converted3 == True, "Should convert 150 to 1.5"
    
    # Test 4: Value of 0.5 (should stay 0.5, already decimal)
    tracker4 = ConversionTracker()
    result4, converted4 = safe_percentage_conversion(0.5, "test_edge4", "test", tracker4)
    assert result4 == 0.5, f"Expected 0.5 (already decimal), got {result4}"
    assert converted4 == False, "Should not convert 0.5"
    
    print("✓ Edge case tests passed")

def test_full_flow():
    """Test that conversion only happens once through full flow"""
    tracker = ConversionTracker()
    
    # Simulate value flowing through system
    original_value = "25%"
    
    # Stage 1: resolve_value
    value1, _ = safe_percentage_conversion(original_value, "test_flow", "resolve_value", tracker)
    assert value1 == 0.25
    
    # Stage 2: apply_fallback (should not convert again)
    value2, _ = safe_percentage_conversion(value1, "test_flow", "apply_fallback", tracker)
    assert value2 == 0.25
    
    # Stage 3: evaluate_formula (should not convert again)
    value3, _ = safe_percentage_conversion(value2, "test_flow", "evaluate_formula", tracker)
    assert value3 == 0.25
    
    # Stage 4: write_to_generated_reports (should not convert again)
    value4, _ = safe_percentage_conversion(value3, "test_flow", "write_to_generated_reports", tracker)
    assert value4 == 0.25
    
    # Check that only one conversion happened
    assert len(tracker.conversion_log) == 1, f"Expected 1 conversion, got {len(tracker.conversion_log)}"
    
    print("✓ Full flow test passed - only one conversion occurred")

def test_tracker_reset():
    """Test that tracker reset works correctly"""
    tracker = ConversionTracker()
    
    # Convert a value
    safe_percentage_conversion(25, "test_var", "stage1", tracker)
    assert tracker.is_converted("test_var"), "Should be marked as converted"
    
    # Reset tracker
    tracker.reset_for_new_calculation()
    assert not tracker.is_converted("test_var"), "Should not be marked after reset"
    assert len(tracker.conversion_log) == 0, "Log should be empty after reset"
    
    print("✓ Tracker reset test passed")

def main():
    print("Running percentage conversion tests...")
    print("=" * 50)
    
    try:
        test_percentage_conversion()
        test_edge_cases()
        test_full_flow()
        test_tracker_reset()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("The conversion tracking solution is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
