# 🚀 GitHub Actions Headshot Sync Setup

## Why GitHub Actions > Cron Jobs?

| Feature | Cron Jobs | GitHub Actions |
|---------|-----------|----------------|
| **Infrastructure** | ❌ Requires server | ✅ Cloud-based |
| **Monitoring** | ❌ Basic logs | ✅ Web dashboard |
| **Notifications** | ❌ Manual setup | ✅ Built-in alerts |
| **Security** | ❌ Local secrets | ✅ Encrypted secrets |
| **Scheduling** | ✅ Flexible | ✅ Native cron syntax |
| **Version Control** | ❌ Not tracked | ✅ Git-based |
| **Manual Triggers** | ❌ SSH required | ✅ One-click |

## 🔧 Setup Instructions

### 1. Repository Secrets

Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

```
AIRTABLE_API_KEY = your_airtable_api_key
AIRTABLE_BASE_ID = your_airtable_base_id
```

> 💡 **Note**: `GITHUB_TOKEN` is automatically provided by GitHub Actions

### 2. Workflow Files

Two workflow options are available:

#### Option A: Simple Workflow
- **File**: `.github/workflows/headshot-sync.yml`
- **Features**: Basic sync with error handling
- **Best for**: Simple setups

#### Option B: Enhanced Workflow  
- **File**: `.github/workflows/headshot-sync-enhanced.yml`
- **Features**: Advanced monitoring, auto-issue creation, detailed logging
- **Best for**: Production environments

### 3. Schedule Configuration

Current schedule: **Every Monday at 6:00 AM UTC**

```yaml
schedule:
  - cron: '0 6 * * 1'
```

**To change timing:**
```yaml
# Daily at 2 AM UTC
- cron: '0 2 * * *'

# Every 6 hours
- cron: '0 */6 * * *'

# Wednesdays at 3 PM UTC
- cron: '0 15 * * 3'
```

## 🎯 Features

### ✅ **Automatic Scheduling**
- Runs every Monday at 6 AM UTC
- No server maintenance required
- Reliable cloud execution

### ✅ **Manual Triggering**
- Run anytime from Actions tab
- Force update option available
- Perfect for testing

### ✅ **Smart Monitoring**
- Automatic issue creation on failures
- Auto-close issues when fixed
- Detailed run summaries

### ✅ **Comprehensive Logging**
- Web-based log viewer
- Downloadable log artifacts
- 30-day retention

### ✅ **Failure Notifications**
- Auto-create GitHub issues
- Email notifications (if configured)
- Slack integration possible

## 🧪 Testing

### Test the Workflow
1. Go to **Actions** tab in your repo
2. Click **"Headshot Sync"** workflow
3. Click **"Run workflow"**
4. Choose **"Run workflow"** button

### Monitor Results
- **Logs**: Available in the workflow run
- **Status**: Green checkmark = success
- **Issues**: Auto-created on failures
- **Artifacts**: Downloadable logs

## 📊 Monitoring Dashboard

The enhanced workflow provides:

### Run Summary
```
📸 Headshot Sync Summary
- Date: 2025-07-17 06:00:00 UTC
- Sync Status: ✅ Success
- Health Check: ✅ Healthy
- Logs: Available in workflow artifacts
```

### Automatic Issue Management
- 🚨 **Failure**: Creates detailed issue with troubleshooting steps
- ✅ **Recovery**: Auto-closes issue when sync succeeds again
- 🏷️ **Labels**: `bug`, `headshot-sync`, `automated`

## 🔒 Security Benefits

- **Encrypted secrets**: API keys stored securely
- **Limited permissions**: Only necessary GitHub access
- **Audit trail**: All runs logged and tracked
- **No local storage**: No sensitive data on servers

## 🚀 Migration from Cron Jobs

1. **Remove cron job**: `crontab -e` and delete the line
2. **Add secrets**: Configure repository secrets
3. **Push workflows**: Commit the `.github/workflows/` files
4. **Test**: Run manually to verify setup
5. **Monitor**: Check logs and notifications

## 📈 Advanced Features

### Force Update Option
```yaml
workflow_dispatch:
  inputs:
    force_update:
      description: 'Force update all headshots'
      type: boolean
      default: false
```

### Slack Notifications
Add to workflow for Slack alerts:
```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Email Notifications
GitHub will email you on workflow failures if:
- You're watching the repository
- You have email notifications enabled

## 🎉 Benefits Achieved

✅ **No more server dependency**  
✅ **Professional monitoring**  
✅ **Automatic failure alerts**  
✅ **One-click manual runs**  
✅ **Version-controlled workflows**  
✅ **Free for public repositories**  
✅ **Better security**  
✅ **Comprehensive logging**  

The GitHub Actions approach is significantly more robust and maintainable than cron jobs!
