"""
Airtable Dependency Updater

This script reads dependency_analysis.json and updates the Calculation Depth field in Airtable for each variable.
"""

import os
import json
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
REPORT_VARIABLES_TABLE = 'Report_Variables'

if not AIRTABLE_API_KEY or not BASE_ID:
    raise ValueError("Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID.")

# Load dependency analysis
try:
    with open('dependency_analysis.json', 'r') as f:
        analysis = json.load(f)
    variable_levels = analysis['variable_levels']
except Exception as e:
    print(f"✗ Error loading dependency_analysis.json: {e}")
    exit(1)

# Connect to Airtable
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)
report_vars_table = base.table(REPORT_VARIABLES_TABLE)

# Get all Report_Variables records
try:
    records = report_vars_table.all()
except Exception as e:
    print(f"✗ Error fetching records from Airtable: {e}")
    exit(1)

# Load previous variables for change detection
PREVIOUS_VARS_FILE = 'previous_variables.json'
try:
    with open(PREVIOUS_VARS_FILE, 'r') as f:
        previous_vars = set(json.load(f))
except Exception:
    previous_vars = set()

# Build updates
updates = []
level_counts = {}
current_vars = set(variable_levels.keys())
new_vars = current_vars - previous_vars

for record in records:
    var_id = record['fields'].get('Variable_ID')
    if var_id in variable_levels:
        level = variable_levels[var_id]
        level_str = f'Level {level}'
        updates.append({
            'id': record['id'],
            'fields': {
                'Calculation Depth': level_str
            }
        })
        level_counts[level_str] = level_counts.get(level_str, 0) + 1

# Save current variables for next run
with open(PREVIOUS_VARS_FILE, 'w') as f:
    json.dump(sorted(list(current_vars)), f, indent=2)

# Batch update
if updates:
    try:
        report_vars_table.batch_update(updates)
        print(f"✓ Updated {len(updates)} records in Airtable.")
        for lvl, count in sorted(level_counts.items()):
            print(f"  {lvl}: {count} records")
        if new_vars:
            print("New variables added since last run:")
            for var in sorted(new_vars):
                print(f"  - {var}")
    except Exception as e:
        print(f"✗ Error updating records in Airtable: {e}")
else:
    print("No records to update.")
