#!/usr/bin/env python3
"""
GitHub Secrets Setup Helper
This script helps you set up the required GitHub repository secrets for the headshot sync workflow.
"""

import os
import sys
import json
from typing import Dict, Optional

def load_env_file(filepath: str = ".env") -> Dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def get_github_repo_info() -> Optional[str]:
    """Get GitHub repository information from environment or git config."""
    # Try from environment first
    env_vars = load_env_file()
    if 'GITHUB_REPO' in env_vars:
        return env_vars['GITHUB_REPO']
    
    # Try from git config
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract owner/repo from Git URL
            if 'github.com/' in url:
                parts = url.split('github.com/')[-1].replace('.git', '')
                return parts
    except:
        pass
    
    return None

def generate_github_cli_commands(env_vars: Dict[str, str], repo: str) -> str:
    """Generate GitHub CLI commands to set secrets."""
    commands = []
    commands.append("# GitHub CLI commands to set repository secrets")
    commands.append(f"# Repository: {repo}")
    commands.append("")
    
    # Required secrets for the workflow
    required_secrets = {
        'AIRTABLE_API_KEY': env_vars.get('AIRTABLE_API_KEY', ''),
        'AIRTABLE_BASE_ID': env_vars.get('AIRTABLE_BASE_ID', ''),
    }
    
    for secret_name, secret_value in required_secrets.items():
        if secret_value:
            commands.append(f'gh secret set {secret_name} --body "{secret_value}" --repo {repo}')
        else:
            commands.append(f'# gh secret set {secret_name} --body "YOUR_VALUE_HERE" --repo {repo}')
    
    commands.append("")
    commands.append("# Note: GITHUB_TOKEN is automatically provided by GitHub Actions")
    commands.append("# Note: GITHUB_REPO will use the automatic github.repository variable")
    
    return "\n".join(commands)

def generate_manual_instructions(env_vars: Dict[str, str], repo: str) -> str:
    """Generate manual setup instructions."""
    instructions = []
    instructions.append("# Manual GitHub Secrets Setup")
    instructions.append(f"# Repository: {repo}")
    instructions.append("")
    instructions.append("1. Go to your GitHub repository")
    instructions.append("2. Click Settings → Secrets and variables → Actions")
    instructions.append("3. Click 'New repository secret' for each of the following:")
    instructions.append("")
    
    required_secrets = {
        'AIRTABLE_API_KEY': env_vars.get('AIRTABLE_API_KEY', ''),
        'AIRTABLE_BASE_ID': env_vars.get('AIRTABLE_BASE_ID', ''),
    }
    
    for secret_name, secret_value in required_secrets.items():
        instructions.append(f"   Name: {secret_name}")
        if secret_value:
            instructions.append(f"   Value: {secret_value}")
        else:
            instructions.append(f"   Value: [PLEASE SET YOUR VALUE]")
        instructions.append("")
    
    instructions.append("Note: GITHUB_TOKEN is automatically provided by GitHub Actions")
    
    return "\n".join(instructions)

def main():
    print("🔧 GitHub Secrets Setup Helper")
    print("=" * 50)
    
    # Load environment variables
    env_vars = load_env_file()
    if not env_vars:
        print("❌ No .env file found. Please create one with your configuration.")
        sys.exit(1)
    
    # Get repository information
    repo = get_github_repo_info()
    if not repo:
        print("❌ Could not determine GitHub repository. Please check your git config or .env file.")
        sys.exit(1)
    
    print(f"📍 Repository: {repo}")
    print(f"📋 Found {len(env_vars)} environment variables")
    print()
    
    # Check required variables
    required_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
    missing_vars = [var for var in required_vars if var not in env_vars or not env_vars[var]]
    
    if missing_vars:
        print(f"⚠️  Missing required variables: {', '.join(missing_vars)}")
        print("Please add these to your .env file first.")
        print()
    
    # Generate GitHub CLI commands
    print("🚀 GitHub CLI Commands (Recommended):")
    print("-" * 40)
    cli_commands = generate_github_cli_commands(env_vars, repo)
    print(cli_commands)
    print()
    
    # Generate manual instructions
    print("📋 Manual Setup Instructions:")
    print("-" * 40)
    manual_instructions = generate_manual_instructions(env_vars, repo)
    print(manual_instructions)
    print()
    
    # Save to file
    with open("github_secrets_setup.txt", "w") as f:
        f.write("GitHub Secrets Setup\n")
        f.write("=" * 50 + "\n\n")
        f.write(cli_commands + "\n\n")
        f.write(manual_instructions + "\n")
    
    print("💾 Setup instructions saved to: github_secrets_setup.txt")
    print()
    print("🎯 Next Steps:")
    print("1. Run the GitHub CLI commands above, OR")
    print("2. Follow the manual setup instructions")
    print("3. Test the workflow: Go to Actions → Headshot Sync → Run workflow")

if __name__ == "__main__":
    main()
