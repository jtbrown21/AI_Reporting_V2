#!/usr/bin/env python3
"""
Debug script to find records with headshots
"""
import os
import sys
from pathlib import Path
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
GENERATED_REPORTS_TABLE = 'Generated_Reports'

def find_records_with_headshots():
    """Find records that have headshots"""
    print("🔍 Looking for records with headshots...")
    
    if not AIRTABLE_API_KEY or not BASE_ID:
        print("❌ Missing AIRTABLE_API_KEY or BASE_ID in environment")
        return
    
    try:
        api = Api(AIRTABLE_API_KEY)
        base = api.base(BASE_ID)
        table = base.table(GENERATED_REPORTS_TABLE)
        
        # Get all records
        records = table.all()
        print(f"📊 Found {len(records)} total records")
        
        # Check each record for headshots
        records_with_headshots = []
        for record in records:
            record_id = record['id']
            fields = record.get('fields', {})
            
            # Check for client_headshot field
            client_headshot = fields.get('client_headshot')
            client_name = fields.get('client_name', 'Unknown')
            
            if client_headshot:
                records_with_headshots.append({
                    'id': record_id,
                    'client_name': client_name,
                    'headshot_data': client_headshot
                })
                print(f"✅ {client_name} ({record_id}) has headshot")
                
                # Show headshot data structure
                if isinstance(client_headshot, list):
                    print(f"   📷 Headshot is a list with {len(client_headshot)} item(s)")
                    if client_headshot:
                        first_item = client_headshot[0]
                        if isinstance(first_item, dict) and 'url' in first_item:
                            print(f"   🔗 First URL: {first_item['url'][:50]}...")
                elif isinstance(client_headshot, dict) and 'url' in client_headshot:
                    print(f"   🔗 URL: {client_headshot['url'][:50]}...")
                elif isinstance(client_headshot, str):
                    print(f"   📝 String data: {client_headshot[:50]}...")
                else:
                    print(f"   ❓ Unknown format: {type(client_headshot)}")
            else:
                print(f"❌ {client_name} ({record_id}) has no headshot")
        
        print(f"\n📋 Summary: {len(records_with_headshots)} records have headshots")
        
        if records_with_headshots:
            print("\n🎯 Records you can test with:")
            for record in records_with_headshots:
                print(f"   {record['client_name']}: {record['id']}")
        else:
            print("\n⚠️  No records found with headshots. You may need to:")
            print("   1. Add headshots to some client records in Airtable")
            print("   2. Check if the field name is correct (looking for 'client_headshot')")
            print("   3. Verify the data has been synced to Generated_Reports table")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_records_with_headshots()
