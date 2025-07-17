#!/usr/bin/env python3
"""
Script to clean up broken headshot files from GitHub repository
"""

import os
import github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')

def cleanup_broken_headshots():
    """Remove broken headshot files from GitHub repository"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("❌ GitHub credentials not found")
        return
    
    try:
        # Initialize GitHub client
        github_client = github.Github(GITHUB_TOKEN)
        repo = github_client.get_repo(GITHUB_REPO)
        
        # List of known broken files
        broken_files = [
            "assets/headshots/greg-aldridge-headshot.jpg"
        ]
        
        for file_path in broken_files:
            try:
                # Get the file
                file_content = repo.get_contents(file_path)
                
                # Handle case where get_contents returns a list
                if isinstance(file_content, list):
                    file_content = file_content[0]
                
                # Delete the file
                repo.delete_file(
                    path=file_path,
                    message=f"Remove broken headshot: {file_path}",
                    sha=file_content.sha
                )
                print(f"✅ Deleted broken file: {file_path}")
                
            except github.GithubException as e:
                if e.status == 404:
                    print(f"ℹ️  File not found: {file_path}")
                else:
                    print(f"❌ Error deleting {file_path}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error with {file_path}: {e}")
        
        print("\n🧹 Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error accessing repository: {e}")

if __name__ == "__main__":
    cleanup_broken_headshots()
