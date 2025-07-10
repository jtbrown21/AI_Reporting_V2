#!/usr/bin/env python3
"""
Test script to verify the GitHub API deployment implementation
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent / "scripts"))

from report_generator import ReportGenerator
from dotenv import load_dotenv

def test_github_api_deployment():
    """Test the GitHub API deployment methods"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if GitHub credentials are configured
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')
    
    if not github_token or not github_repo:
        print("✗ GitHub credentials not configured")
        print("Please set GITHUB_TOKEN and GITHUB_REPO environment variables")
        return False
    
    print(f"Testing GitHub API deployment with repo: {github_repo}")
    
    # Create a ReportGenerator instance
    try:
        generator = ReportGenerator(test_mode=True)
        print("✓ ReportGenerator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize ReportGenerator: {e}")
        return False
    
    # Test 1: Check GitHub client initialization
    print("\n=== Test 1: GitHub Client Initialization ===")
    if generator.github_client:
        print("✓ GitHub client initialized successfully")
    else:
        print("✗ GitHub client not initialized")
        return False
    
    # Test 2: Test repository access
    print("\n=== Test 2: Repository Access ===")
    try:
        repo = generator.github_client.get_repo(generator.github_repo)
        print(f"✓ Repository accessed successfully: {repo.name}")
    except Exception as e:
        print(f"✗ Failed to access repository: {e}")
        return False
    
    # Test 3: Test file publishing
    print("\n=== Test 3: File Publishing ===")
    test_content = f"""
    <html>
    <head>
        <title>Test Report</title>
    </head>
    <body>
        <h1>Test Report</h1>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>This is a test report to verify GitHub API deployment.</p>
    </body>
    </html>
    """
    
    test_filename = f"test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    test_path = f"reports/{test_filename}"
    commit_message = f"Test GitHub API deployment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        success = generator.publish_report_to_github(test_content, test_path, commit_message)
        if success:
            print(f"✓ Test report published successfully to {test_path}")
        else:
            print(f"✗ Failed to publish test report")
            return False
    except Exception as e:
        print(f"✗ Error publishing test report: {e}")
        return False
    
    # Test 4: Test full deployment method
    print("\n=== Test 4: Full Deployment Method ===")
    try:
        url = generator.deploy_to_github_via_api(test_content, test_filename)
        if url:
            print(f"✓ Full deployment successful: {url}")
        else:
            print("✗ Full deployment failed")
            return False
    except Exception as e:
        print(f"✗ Error in full deployment: {e}")
        return False
    
    print("\n=== All Tests Passed! ===")
    print("GitHub API deployment is working correctly.")
    return True

if __name__ == "__main__":
    success = test_github_api_deployment()
    sys.exit(0 if success else 1)
