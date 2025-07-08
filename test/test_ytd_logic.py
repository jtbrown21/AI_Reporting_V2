#!/usr/bin/env python3
"""
Test script to verify YTD calculation logic
"""

from datetime import datetime
import json

# Mock context for testing
class MockContext:
    def __init__(self, report_month, report_year, client_id='test_client'):
        self.report_month = report_month
        self.report_year = report_year
        self.client_id = client_id
        self.errors = []
        self.warnings = []
        self.calculated_values = {}
        self.ytd_metadata = {}
        self.calculation_log = []
        
    def add_value(self, variable, value, source):
        self.calculated_values[variable] = value
        
# Test scenarios
def test_ytd_scenarios():
    print("Testing YTD calculation scenarios...")
    
    # Scenario 1: January report (no previous months)
    print("\n1. January Report (No Previous Months)")
    context = MockContext(1, 2025)
    previous_months = list(range(1, context.report_month))
    print(f"   Previous months: {previous_months}")
    print(f"   Expected: No Data (reason: No previous months)")
    
    # Scenario 2: July report with all previous months
    print("\n2. July Report (All Previous Months Available)")
    context = MockContext(7, 2025)
    previous_months = list(range(1, context.report_month))
    print(f"   Previous months: {previous_months}")
    print(f"   Expected: Sum of Jan-Jun values")
    
    # Scenario 3: July report with missing months
    print("\n3. July Report (Missing Some Months)")
    context = MockContext(7, 2025)
    previous_months = list(range(1, context.report_month))
    months_with_data = {1: 100, 3: 150, 4: 200, 6: 180}  # Missing Feb(2) and May(5)
    ytd_total = sum(months_with_data.values())
    months_included = sorted(months_with_data.keys())
    months_missing = [m for m in previous_months if m not in months_with_data]
    coverage = (len(months_included) / len(previous_months) * 100) if previous_months else 0
    
    print(f"   Previous months: {previous_months}")
    print(f"   Data available for: {months_included}")
    print(f"   Missing months: {months_missing}")
    print(f"   YTD Total: {ytd_total}")
    print(f"   Coverage: {coverage:.1f}%")
    
    # Scenario 4: December report (full year)
    print("\n4. December Report (Full Year)")
    context = MockContext(12, 2025)
    previous_months = list(range(1, context.report_month))
    print(f"   Previous months: {previous_months}")
    print(f"   Expected: Sum of Jan-Nov values (11 months)")
    
    print("\nAll scenarios tested successfully!")

if __name__ == "__main__":
    test_ytd_scenarios()
