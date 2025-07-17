# Headshot Sync Cron Job Setup Instructions

## 🕐 Weekly Headshot Sync Schedule

To set up the weekly headshot sync cron job, follow these steps:

### 1. Open crontab
```bash
crontab -e
```

### 2. Add the following line
```bash
# Weekly headshot sync - Every Monday at 6:00 AM
0 6 * * 1 /Users/jtbrown/AgentInsider/AI_Reporting_V2/scripts/run_headshot_sync.sh >> /Users/jtbrown/AgentInsider/AI_Reporting_V2/logs/cron.log 2>&1
```

### 3. Save and exit
- In vim: Press `Esc`, then `:wq`
- In nano: Press `Ctrl+X`, then `Y`, then `Enter`

### 4. Verify the cron job is installed
```bash
crontab -l
```

## 📋 Schedule Explanation

| Field | Value | Description |
|-------|-------|-------------|
| Minute | 0 | At minute 0 |
| Hour | 6 | At 6 AM |
| Day of Month | * | Every day of the month |
| Month | * | Every month |
| Day of Week | 1 | On Monday (1=Monday, 0=Sunday) |

## 📂 Log Files

- **Sync logs**: `/Users/jtbrown/AgentInsider/AI_Reporting_V2/logs/headshot_sync_YYYYMMDD.log`
- **Cron logs**: `/Users/jtbrown/AgentInsider/AI_Reporting_V2/logs/cron.log`

## 🧪 Testing the Cron Job

To test the cron job manually:
```bash
/Users/jtbrown/AgentInsider/AI_Reporting_V2/scripts/run_headshot_sync.sh
```

## 📊 Monitoring

Check the status of the sync:
```bash
# View recent sync logs
tail -f /Users/jtbrown/AgentInsider/AI_Reporting_V2/logs/cron.log

# Check headshot status
python3 /Users/jtbrown/AgentInsider/AI_Reporting_V2/scripts/check_headshot_status.py
```

## 🔧 Alternative Schedules

If you need different timing:

```bash
# Every day at 2 AM
0 2 * * * /path/to/run_headshot_sync.sh

# Every Sunday at 11 PM
0 23 * * 0 /path/to/run_headshot_sync.sh

# Every 6 hours
0 */6 * * * /path/to/run_headshot_sync.sh
```

## 🚨 Troubleshooting

If the cron job doesn't run:

1. **Check cron service**: `sudo systemctl status cron` (Linux) or `sudo launchctl list | grep cron` (macOS)
2. **Check permissions**: Ensure the script is executable (`chmod +x run_headshot_sync.sh`)
3. **Check paths**: Verify all paths in the script are absolute
4. **Check environment**: Cron runs with limited environment variables
5. **Check logs**: Look at both cron.log and the daily sync logs

## ✅ Success Indicators

The cron job is working if you see:
- New log files created daily in the logs directory
- "✅ Headshot sync completed successfully" in the logs
- Updated manifest.json with recent timestamps
- No error messages in cron.log
