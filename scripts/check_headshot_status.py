#!/usr/bin/env python3
"""
Headshot Status Check Script

This script verifies that the headshot sync is working correctly by:
1. Reading the manifest from GitHub Pages
2. Checking sync status and timing
3. Identifying any issues with headshot processing

Run this script to quickly verify the health of the headshot sync system.
"""

import os
import json
import requests
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_manifest() -> Dict[str, Any]:
    """Fetch manifest from GitHub Pages"""
    try:
        manifest_url = "https://app.agentinsider.co/assets/headshots/manifest.json"
        response = requests.get(manifest_url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch manifest: HTTP {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"❌ Error fetching manifest: {e}")
        return {}

def check_sync_status(manifest: Dict[str, Any]) -> bool:
    """Check if sync is current and healthy"""
    try:
        last_sync = manifest.get('last_sync')
        if not last_sync:
            print("❌ No sync timestamp found in manifest")
            return False
            
        # Parse last sync time
        last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
        current_time = datetime.now()
        
        # Check if sync is older than 7 days
        if (current_time - last_sync_time) > timedelta(days=7):
            print(f"⚠️  Last sync was {(current_time - last_sync_time).days} days ago")
            print(f"    Last sync: {last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return False
        else:
            print(f"✅ Last sync: {last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
    except Exception as e:
        print(f"❌ Error checking sync status: {e}")
        return False

def analyze_headshots(manifest: Dict[str, Any]):
    """Analyze headshot data and report findings"""
    headshots = manifest.get('headshots', {})
    
    if not headshots:
        print("❌ No headshots found in manifest")
        return
        
    print(f"📊 Total headshots: {len(headshots)}")
    
    # Check for old headshots
    old_headshots = []
    current_time = datetime.now()
    
    for client_name, data in headshots.items():
        processed_date = data.get('processed_date')
        if processed_date:
            try:
                processed_time = datetime.fromisoformat(processed_date.replace('Z', '+00:00'))
                if (current_time - processed_time) > timedelta(days=7):
                    old_headshots.append({
                        'client': client_name,
                        'days_old': (current_time - processed_time).days
                    })
            except:
                pass
                
    if old_headshots:
        print(f"⚠️  {len(old_headshots)} headshots older than 7 days:")
        for item in old_headshots[:5]:  # Show first 5
            print(f"    - {item['client']}: {item['days_old']} days old")
        if len(old_headshots) > 5:
            print(f"    ... and {len(old_headshots) - 5} more")
    else:
        print("✅ All headshots are current (within 7 days)")

def test_sample_headshots(manifest: Dict[str, Any]):
    """Test accessibility of sample headshots"""
    headshots = manifest.get('headshots', {})
    
    if not headshots:
        return
        
    print(f"\n🔍 Testing sample headshot accessibility...")
    
    # Test up to 3 random headshots
    import random
    sample_clients = random.sample(list(headshots.keys()), min(3, len(headshots)))
    
    for client_name in sample_clients:
        headshot_data = headshots[client_name]
        github_url = headshot_data.get('github_url')
        
        if github_url:
            try:
                response = requests.head(github_url, timeout=5)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        print(f"✅ {client_name}: Accessible ({content_type})")
                    else:
                        print(f"⚠️  {client_name}: Wrong content-type ({content_type})")
                else:
                    print(f"❌ {client_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {client_name}: Error - {e}")

def main():
    """Main function"""
    print("🔍 Headshot Sync Status Check")
    print("=" * 50)
    
    # Get manifest
    manifest = get_manifest()
    if not manifest:
        print("❌ Cannot proceed without manifest")
        sys.exit(1)
        
    # Check sync status
    sync_healthy = check_sync_status(manifest)
    
    # Analyze headshots
    print("\n📋 Headshot Analysis:")
    analyze_headshots(manifest)
    
    # Test sample headshots
    test_sample_headshots(manifest)
    
    # Overall health check
    print("\n🏥 Overall Health:")
    if sync_healthy:
        print("✅ Headshot sync system is healthy")
        sys.exit(0)
    else:
        print("❌ Headshot sync system needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
