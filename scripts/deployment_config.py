"""
Deployment Configuration for Report Generation System

This file contains configuration templates and setup instructions for deploying
the report generation system on Railway with n8n integration.
"""

import os
from pathlib import Path

# Railway deployment configuration
RAILWAY_CONFIG = {
    "name": "ai-reporting-webhook",
    "start_command": "python scripts/webhook_server.py",
    "build_command": "pip install -r requirements.txt",
    "port": 5000,
    "environment_variables": {
        "AIRTABLE_API_KEY": "your-airtable-api-key",
        "AIRTABLE_BASE_ID": "your-airtable-base-id",
        "GITHUB_TOKEN": "your-github-token",
        "GITHUB_REPO": "your-username/your-repo",
        "GITHUB_PAGES_BRANCH": "gh-pages",
        "WEBHOOK_SECRET": "your-webhook-secret",
        "PORT": "5000",
        "FLASK_DEBUG": "False"
    }
}

# n8n workflow configuration
N8N_WORKFLOW_CONFIG = {
    "name": "Report Generation Workflow",
    "trigger": {
        "type": "Airtable Trigger",
        "description": "Triggers when a new record is created in Client_Reports"
    },
    "nodes": [
        {
            "name": "Airtable Trigger",
            "type": "airtable-trigger",
            "parameters": {
                "base_id": "your-airtable-base-id",
                "table_name": "Client_Reports",
                "event": "record_created"
            }
        },
        {
            "name": "HTTP Request",
            "type": "http-request",
            "parameters": {
                "url": "https://your-railway-app.railway.app/webhook/generate-report",
                "method": "POST",
                "headers": {
                    "X-Webhook-Secret": "your-webhook-secret",
                    "Content-Type": "application/json"
                },
                "body": {
                    "report_id": "{{ $json.record_id }}"
                }
            }
        }
    ]
}

def create_env_file():
    """Create a .env file template"""
    env_content = """# Airtable Configuration
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-airtable-base-id

# GitHub Configuration
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/your-repo
GITHUB_PAGES_BRANCH=gh-pages

# Webhook Configuration
WEBHOOK_SECRET=your-webhook-secret

# Flask Configuration
PORT=5000
FLASK_DEBUG=False
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_content)
    
    print("✓ Created .env.template file")
    print("Please copy to .env and fill in your actual values")

def create_railway_config():
    """Create Railway configuration files"""
    
    # Create Procfile
    with open('Procfile', 'w') as f:
        f.write("web: python scripts/webhook_server.py\n")
    
    # Create railway.json
    railway_json = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python scripts/webhook_server.py",
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    import json
    with open('railway.json', 'w') as f:
        json.dump(railway_json, f, indent=2)
    
    print("✓ Created Railway configuration files")
    print("  - Procfile")
    print("  - railway.json")

def update_requirements():
    """Update requirements.txt with additional dependencies"""
    new_requirements = [
        "pyairtable==2.1.0",
        "python-dotenv==1.0.0",
        "pandas==2.1.4",
        "flask==2.3.3",
        "requests==2.31.0"
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(new_requirements) + '\n')
    
    print("✓ Updated requirements.txt with Flask and additional dependencies")

def create_github_pages_setup():
    """Create GitHub Pages setup instructions"""
    setup_content = """# GitHub Pages Setup for Report Hosting

## 1. Create GitHub Repository
1. Create a new GitHub repository for hosting reports
2. Go to repository Settings > Pages
3. Set source to "Deploy from a branch"
4. Select "gh-pages" branch
5. Click Save

## 2. Generate GitHub Token
1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate a new token with these permissions:
   - repo (full control)
   - workflow
3. Copy the token for use in environment variables

## 3. Repository Structure
Your repository should have this structure:
```
your-repo/
├── index.html (latest report)
├── client-name-2024-01-01.html
├── client-name-2024-02-01.html
└── ...
```

## 4. Environment Variables
Set these in your Railway deployment:
- GITHUB_TOKEN: Your GitHub token
- GITHUB_REPO: username/repository-name
- GITHUB_PAGES_BRANCH: gh-pages (or main if you prefer)

## 5. Test Access
Your reports will be available at:
- https://username.github.io/repository-name/
- https://username.github.io/repository-name/specific-report.html
"""
    
    with open('GITHUB_PAGES_SETUP.md', 'w') as f:
        f.write(setup_content)
    
    print("✓ Created GitHub Pages setup guide")

def create_n8n_workflow_template():
    """Create n8n workflow template"""
    workflow_content = """# n8n Workflow Template for Report Generation

## Workflow Overview
This n8n workflow automatically generates reports when new records are created in Airtable.

## Nodes:

### 1. Airtable Trigger
- **Node Type**: Airtable Trigger
- **Base ID**: your-airtable-base-id
- **Table**: Client_Reports
- **Event**: Record Created

### 2. HTTP Request to Railway
- **Node Type**: HTTP Request
- **URL**: https://your-railway-app.railway.app/webhook/generate-report
- **Method**: POST
- **Headers**:
  - X-Webhook-Secret: your-webhook-secret
  - Content-Type: application/json
- **Body**:
  ```json
  {
    "report_id": "{{ $json.record_id }}"
  }
  ```

### 3. Optional: Notification
- **Node Type**: Slack/Email/etc.
- **Message**: "Report generated for {{ $json.report_id }}"

## Alternative: Manual Trigger
Instead of automatic trigger, you can create a manual workflow:

1. **Manual Trigger** with report_id parameter
2. **HTTP Request** to webhook endpoint
3. **Notification** with result

## Webhook Endpoints Available:
- `/webhook/generate-report` - Async report generation
- `/webhook/generate-report-sync` - Sync report generation
- `/webhook/calculation-only` - Run calculations only
- `/webhook/deploy-only` - Deploy report only
"""
    
    with open('N8N_WORKFLOW_TEMPLATE.md', 'w') as f:
        f.write(workflow_content)
    
    print("✓ Created n8n workflow template")

def main():
    """Setup deployment configuration"""
    print("Setting up report generation deployment configuration...")
    
    create_env_file()
    create_railway_config()
    update_requirements()
    create_github_pages_setup()
    create_n8n_workflow_template()
    
    print("\n✓ Deployment configuration complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and fill in your values")
    print("2. Set up GitHub repository and Pages (see GITHUB_PAGES_SETUP.md)")
    print("3. Deploy to Railway using the generated config files")
    print("4. Set up n8n workflow using N8N_WORKFLOW_TEMPLATE.md")
    print("5. Test the webhook endpoints")

if __name__ == "__main__":
    main()
