#!/usr/bin/env python3
"""
Test the YTD calculation fix
"""

import os
import sys
sys.path.append('/Users/jtbrown/AgentInsider/AI_Reporting_V2/scripts')

from calculation_engine import main

# Test with the specific record that should have YTD calculation
test_record_id = 'reccNSoJ9evk5s0PE'

print("Testing YTD calculation fix...")
print(f"Running calculation for record: {test_record_id}")

# Run the calculation engine
main(test_record_id)

print("Test complete!")
