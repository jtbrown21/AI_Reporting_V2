#!/usr/bin/env python3
"""
Quick test script to verify GitHub authentication works
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent / "scripts"))

from report_generator import ReportGenerator
from dotenv import load_dotenv

def test_github_auth():
    """Test GitHub authentication"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if GitHub credentials are configured
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')
    
    print(f"GITHUB_TOKEN: {'Set' if github_token else 'Not set'}")
    print(f"GITHUB_REPO: {github_repo}")
    
    if not github_token:
        print("❌ GITHUB_TOKEN is not set")
        return False
    
    if not github_repo:
        print("❌ GITHUB_REPO is not set")
        return False
    
    try:
        # Create a ReportGenerator instance
        generator = ReportGenerator(test_mode=True)
        
        if not generator.github_client:
            print("❌ GitHub client not initialized")
            return False
        
        # Test repository access
        repo = generator.github_client.get_repo(generator.github_repo)
        print(f"✅ Successfully connected to repository: {repo.name}")
        
        # Test token permissions by trying to get repository info
        print(f"Repository URL: {repo.html_url}")
        print(f"Repository permissions: push={repo.permissions.push}, admin={repo.permissions.admin}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing GitHub Authentication...")
    print("=" * 50)
    
    success = test_github_auth()
    
    if success:
        print("\n✅ GitHub authentication test passed!")
        print("Your local setup is working correctly.")
        print("\nIf you're still getting 401 errors on Railway:")
        print("1. Check that GITHUB_TOKEN is set in Railway's environment variables")
        print("2. Make sure the token hasn't expired")
        print("3. Verify the token has 'repo' and 'workflow' permissions")
    else:
        print("\n❌ GitHub authentication test failed!")
        print("Please check your GitHub token and repository configuration.")
