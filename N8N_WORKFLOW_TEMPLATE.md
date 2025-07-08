# n8n Workflow Template for Report Generation

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
