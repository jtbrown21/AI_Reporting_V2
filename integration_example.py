"""
Report Generation Integration Script

This script demonstrates how to integrate the report generation system
with your existing calculation engine workflow.
"""

import os
import sys
import json
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.append(str(Path(__file__).parent / "scripts"))

from dotenv import load_dotenv
load_dotenv()

def integrate_with_calculation_engine():
    """Example of integrating report generation with calculation engine"""
    
    print("Report Generation System Integration Example")
    print("="*50)
    
    # Example: After running calculation engine, generate report
    report_id = "recABC123"  # Replace with actual report ID
    
    try:
        # Import here to avoid import errors if modules aren't available
        from report_generator import ReportGenerator
        
        # Create report generator
        generator = ReportGenerator()
        
        # Generate and deploy report
        print(f"Generating report for {report_id}...")
        url = generator.generate_and_deploy(report_id)
        
        if url:
            print(f"✓ Report generated successfully: {url}")
            
            # Example: Send notification or update database
            # send_notification(url)
            # update_database(report_id, url)
            
        else:
            print("✗ Report generation failed")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"✗ Error: {e}")

def example_webhook_usage():
    """Example of using webhook endpoints"""
    
    print("\nWebhook Integration Example")
    print("="*30)
    
    webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000')
    webhook_secret = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret')
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Available endpoints:")
    print(f"  POST {webhook_url}/webhook/generate-report")
    print(f"  POST {webhook_url}/webhook/generate-report-sync")
    print(f"  POST {webhook_url}/webhook/calculation-only")
    print(f"  POST {webhook_url}/webhook/deploy-only")
    print(f"  GET  {webhook_url}/health")

def example_n8n_configuration():
    """Example n8n workflow configuration"""
    
    print("\nn8n Workflow Configuration Example")
    print("="*40)
    
    n8n_config = {
        "nodes": [
            {
                "name": "Airtable Trigger",
                "type": "airtable-trigger",
                "description": "Triggers when new record is created",
                "parameters": {
                    "base_id": "your-airtable-base-id",
                    "table_name": "Client_Reports",
                    "event": "record_created"
                }
            },
            {
                "name": "HTTP Request",
                "type": "http-request",
                "description": "Calls report generation webhook",
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
            },
            {
                "name": "Slack Notification",
                "type": "slack",
                "description": "Sends notification to Slack",
                "parameters": {
                    "message": "Report generated for {{ $json.report_id }}"
                }
            }
        ]
    }
    
    print("Example n8n workflow configuration:")
    print(json.dumps(n8n_config, indent=2))

def main():
    """Main integration example"""
    
    print("REPORT GENERATION SYSTEM INTEGRATION")
    print("="*60)
    
    # Check environment variables
    required_vars = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID',
        'GITHUB_TOKEN',
        'GITHUB_REPO'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("✗ Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these in your .env file before running the system.")
        return
    
    print("✓ Environment variables configured")
    
    # Run integration examples
    integrate_with_calculation_engine()
    example_webhook_usage()
    example_n8n_configuration()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Set up GitHub repository and Pages")
    print("2. Deploy webhook server to Railway")
    print("3. Configure n8n workflow")
    print("4. Test the integration")
    print("5. Monitor reports and logs")

if __name__ == "__main__":
    main()
