# Automated Report Generation System

This system automates the generation and deployment of HTML reports after running the calculation engine. It integrates with GitHub Pages for hosting and provides webhook endpoints for n8n workflow automation.

## System Architecture

```
Client_Reports (Airtable) → Calculation Engine → Report Generator → GitHub Pages
                                      ↓
                              n8n Workflow → Railway Webhook → Generated Reports
```

## Components

### 1. Report Generator (`report_generator.py`)
- Fetches calculated data from Airtable
- Maps variables to HTML template
- Generates formatted HTML reports
- Deploys to GitHub Pages
- Updates Airtable with report URLs

### 2. Webhook Server (`webhook_server.py`)
- Provides REST API endpoints for n8n integration
- Handles background report processing
- Supports both sync and async operations
- Includes health checks and error handling

### 3. Enhanced Calculation Engine (`enhanced_calculation_engine.py`)
- Extends original calculation engine
- Automatically generates reports after calculations
- Command-line interface for manual operations

### 4. Deployment Configuration (`deployment_config.py`)
- Creates Railway deployment config
- Generates environment templates
- Provides setup instructions

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your values
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-airtable-base-id
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/your-repo
WEBHOOK_SECRET=your-webhook-secret
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Manual Report Generation
```bash
# Run calculation engine and generate report
python scripts/enhanced_calculation_engine.py recABC123

# Generate report only (calculations already done)
python scripts/report_generator.py recABC123

# Run calculation engine only
python scripts/calculation_engine.py recABC123
```

### 4. Start Webhook Server
```bash
python scripts/webhook_server.py
```

## Webhook Endpoints

### Health Check
```bash
GET /health
```

### Generate Full Report (Async)
```bash
POST /webhook/generate-report
Headers:
  X-Webhook-Secret: your-webhook-secret
  Content-Type: application/json
Body:
  {
    "report_id": "recABC123"
  }
```

### Generate Full Report (Sync)
```bash
POST /webhook/generate-report-sync
Headers:
  X-Webhook-Secret: your-webhook-secret
  Content-Type: application/json
Body:
  {
    "report_id": "recABC123"
  }
```

### Run Calculation Only
```bash
POST /webhook/calculation-only
Headers:
  X-Webhook-Secret: your-webhook-secret
  Content-Type: application/json
Body:
  {
    "report_id": "recABC123"
  }
```

### Deploy Report Only
```bash
POST /webhook/deploy-only
Headers:
  X-Webhook-Secret: your-webhook-secret
  Content-Type: application/json
Body:
  {
    "report_id": "recABC123"
  }
```

## GitHub Pages Setup

### 1. Create Repository
1. Create a new GitHub repository for hosting reports
2. Go to Settings > Pages
3. Set source to "Deploy from a branch"
4. Select "gh-pages" branch

### 2. Generate GitHub Token
1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate new token with `repo` and `workflow` permissions
3. Add to environment variables

### 3. Repository Structure
```
your-repo/
├── index.html (latest report)
├── client-name-2024-01-01.html
├── client-name-2024-02-01.html
└── ...
```

## Railway Deployment

### 1. Setup Railway Project
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy using auto-deploy or manual trigger

### 2. Environment Variables
```
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-airtable-base-id
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/your-repo
GITHUB_PAGES_BRANCH=gh-pages
WEBHOOK_SECRET=your-webhook-secret
PORT=5000
FLASK_DEBUG=False
```

### 3. Deployment Files
- `Procfile`: Web process command
- `railway.json`: Railway-specific configuration
- `requirements.txt`: Python dependencies

## n8n Workflow Setup

### 1. Basic Workflow
1. **Airtable Trigger**: New record in Client_Reports
2. **HTTP Request**: POST to webhook endpoint
3. **Notification**: Success/failure notification

### 2. Advanced Workflow
1. **Manual Trigger**: With report_id parameter
2. **HTTP Request**: POST to webhook endpoint
3. **Conditional Logic**: Handle success/failure
4. **Multiple Notifications**: Email, Slack, etc.

### 3. Webhook Configuration
- URL: `https://your-railway-app.railway.app/webhook/generate-report`
- Method: POST
- Headers: `X-Webhook-Secret: your-webhook-secret`
- Body: `{"report_id": "{{ $json.record_id }}"}`

## Variable Mapping

The system maps Airtable fields to HTML template variables:

### Template Variables (data-field attributes)
- `new-households` → `hhs`
- `auto-policies` → `est_auto`
- `fire-policies` → `est_fire`
- `annual-commission` → `est_annual_commission`
- `roi` → `year1_return`
- `report-date` → `date_end` (formatted)
- `client-name` → `client_name`

### Field Mapping File
The `field_mapping.json` file controls the mapping between Airtable fields and template variables.

## Error Handling

### Common Issues
1. **Missing Environment Variables**: Check .env file
2. **GitHub Authentication**: Verify token permissions
3. **Airtable Access**: Check API key and base ID
4. **Template Errors**: Verify HTML template syntax

### Debugging
1. Check webhook server logs
2. Verify Airtable record exists
3. Test GitHub Pages deployment manually
4. Validate environment variables

## Testing

### Local Testing
```bash
# Test report generation
python scripts/report_generator.py recABC123

# Test webhook server
python scripts/webhook_server.py

# Test in another terminal
curl -X POST http://localhost:5000/webhook/generate-report-sync \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -H "Content-Type: application/json" \
  -d '{"report_id": "recABC123"}'
```

### Production Testing
```bash
# Test health endpoint
curl https://your-railway-app.railway.app/health

# Test webhook endpoint
curl -X POST https://your-railway-app.railway.app/webhook/generate-report-sync \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -H "Content-Type: application/json" \
  -d '{"report_id": "recABC123"}'
```

## Monitoring

### Logs
- Railway provides built-in logging
- Webhook server logs all requests
- Report generator logs deployment status

### Metrics
- Report generation success rate
- Deployment time
- Error frequency

## Security

### Webhook Security
- Uses secret key validation
- HTTPS only in production
- Rate limiting (implement as needed)

### GitHub Security
- Personal access tokens
- Repository permissions
- Branch protection rules

## Maintenance

### Regular Tasks
1. Update dependencies
2. Monitor GitHub Pages quota
3. Clean up old reports
4. Update environment variables

### Troubleshooting
1. Check Railway logs
2. Verify GitHub Pages status
3. Test Airtable connections
4. Validate webhook endpoints

## Extensions

### Possible Enhancements
1. Multiple report templates
2. Email notifications
3. Report scheduling
4. Analytics dashboard
5. Report archiving
6. Custom domains

### Integration Options
1. Slack notifications
2. Email alerts
3. Database logging
4. Monitoring tools
5. CI/CD pipelines
