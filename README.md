# AI_Reporting_V2
Codebase for V2 of AI Reporting

## Project Structure

```
AI_Reporting_V2/
├── scripts/                    # Core calculation and utility scripts
│   ├── calculation_engine.py   # Main calculation engine
│   ├── dependency_analyzer.py  # Dependency analysis
│   └── validate_field_mapping.py
├── test/                       # Test files and validation scripts
│   ├── test_ytd_logic.py      # YTD calculation tests
│   ├── test_validation_fix.py  # Validation function tests
│   └── ...                    # Other test files
├── logs/                       # Generated calculation logs
│   └── calculation_log_*.json  # Detailed calculation logs per record
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## Field Mapping Validation Script

The `scripts/validate_field_mapping.py` script validates that every variable defined in the `Report_Variables` table has a corresponding field in the `Generated_Reports` table in Airtable.

### What it does
- Checks that each variable in `Report_Variables` exists as a field in `Generated_Reports`.
- Reports missing fields and extra fields.
- (Field type validation is planned for a future update.)

### Requirements
- Python 3.7+
- Install dependencies:
  ```sh
  pip install -r requirements.txt
  ```
- Create a `.env` file in the project root with your Airtable credentials:
  ```
  AIRTABLE_API_KEY=your_actual_api_key
  AIRTABLE_BASE_ID=your_actual_base_id
  ```

### Usage
Run the script from the project root:
```sh
python scripts/validate_field_mapping.py
```

The script will print a summary and save results to `validation_results.json`.

---

## Dependency Analysis & Airtable Update

### 1. Dependency Analyzer

The `scripts/dependency_analyzer.py` script analyzes dependencies between variables in `Report_Variables` and outputs calculation order, depth, and more.

- Output: `dependency_analysis.json` in the project root.
- Usage:
  ```sh
  python scripts/dependency_analyzer.py
  ```

### 2. Airtable Dependency Updater

The `scripts/airtable_dependency_updater.py` script reads `dependency_analysis.json` and updates the `Calculation Depth` field in Airtable for each variable.

- Usage:
  ```sh
  python scripts/airtable_dependency_updater.py
  ```
- The script will print a summary of how many records were updated at each level.

---

## Calculation Engine

The `scripts/calculation_engine.py` script performs comprehensive calculations on report data, including Year-to-Date (YTD) analysis.

### Key Features

- **YTD Calculation**: Automatically calculates Year-to-Date values for `hhs` using historical data
- **Smart Fallback Logic**: Uses current month's `hhs` value when no historical data is available
- **Auto-Detection**: Automatically detects whether a record ID is from `Generated_Reports` (for rerunning) or `Client_Reports`
- **Validation System**: Comprehensive validation of all calculated values against business rules
- **Comprehensive Logging**: Detailed calculation logs and metadata tracking
- **Error Handling**: Graceful handling of missing data and query failures

### YTD Implementation

The engine calculates `hhs_ytd` by:
1. Querying previous full months in the current year from `Generated_Reports`
2. Summing historical `hhs` values for complete YTD calculation
3. **Fallback**: If no historical data exists, uses current month's calculated `hhs` value
4. Storing simplified metadata in `hhs_ytd_metadata` field

### Usage

**Rerun calculations on existing Generated_Reports record:**
```sh
python scripts/calculation_engine.py rec90GpdKkC9hu9jJ
```

**Run without arguments to process pending reports:**
```sh
python scripts/calculation_engine.py
```

### Output

- Updates the existing record in `Generated_Reports` table with:
  - All calculated values (hhs, est_auto, est_fire, etc.)
  - YTD analysis in `hhs_ytd_metadata` field
  - **Enhanced Calculation Log** with comprehensive analysis
  - Validation results and warnings

### Enhanced Calculation Log Format

The `Calculation Log` field now provides detailed analysis for each variable:

**For Each Variable:**
- ✓ Variable name and calculated value
- Formula and step-by-step calculation  
- Fallback tracking (if fallbacks were used)
- Hard validation status (✅ PASS or 🚨 FAIL)
- Expected range validation (✅ PASS, ⚠️ OUTSIDE, or 🚨 FAR OUTSIDE)

**Data Quality Summary:**
- Total variables calculated
- Fallback usage breakdown by type
- Validation statistics and percentages
- Warning summary with severity indicators

**Example Log Entry:**
```
✓ website_hhs = 0.60
  Formula: = {quote_starts} x {%won_website}
  Calculated: 5 * 0.12 = 0.60
  No Fallback (calculated from available data)
  ✅ Valid Range: >= 0 (PASS)
  ⚠️ Expected Range: >= 1 AND <= 5 (OUTSIDE - Low)
```

### YTD Metadata Format

The `hhs_ytd_metadata` field contains simplified JSON:

```json
{
  "reason": "No historical data found, using current month HHS value",
  "months": {
    "1": "missing",
    "2": "missing", 
    "3": "missing",
    "4": "missing",
    "5": "missing"
  },
  "ytd_value": 11.026,
  "current_month_hhs": 11.026
}
```

---

## Validation System

The calculation engine includes a comprehensive validation system that automatically checks all calculated values against business rules defined in the `Report_Variables` table.

### Hard Validation (Red Flags 🔴)
- **Purpose**: Identifies values that violate fundamental business logic
- **Source**: Uses the `Validation_Rules` field in `Report_Variables` table
- **Impact**: Validation failures are logged as errors and may indicate data quality issues
- **Examples**: 
  - `>= 0 AND <= 1` for percentages (must be between 0% and 100%)
  - `>= 0 AND integer` for count fields (must be non-negative whole numbers)
  - `not_empty` for required text fields
  - `> 0 AND <= 0.5` for commission rates (must be positive but reasonable)

### Soft Validation (Yellow Flags 🟡)  
- **Purpose**: Identifies values outside expected business ranges (unusual but potentially valid)
- **Source**: Uses the `Expected_Values` field in `Report_Variables` table
- **Impact**: Out-of-range values are logged as warnings for review
- **Examples**: 
  - `>= 0.09 AND <= 0.25` for conversion rates (typical industry ranges)
  - `>= 10 AND <= 65` for lead counts (normal monthly volumes)
  - `>= 2000 AND <= 3500` for average premiums (expected pricing)
  - `optional` for fields that don't require range validation

### Validation Expression Syntax
The validation system supports complex logical expressions:
- **Comparison operators**: `>=`, `<=`, `>`, `<`, `=`
- **Logical operators**: `AND`, `OR`
- **Special keywords**: `integer`, `not_empty`, `optional`
- **Example**: `>= 0 AND <= 1` or `>= 10 AND <= 65`

### Integration with Calculation Engine
- **Automatic Execution**: Validation runs automatically after all calculations complete
- **Context Integration**: Results stored in `CalculationContext` as `validation_flags` and `expected_flags`
- **Logging**: Validation results appear in:
  - Console output with color-coded summaries
  - Detailed JSON calculation logs
  - Integration with existing error/warning systems

### Validation Output
The validation system provides comprehensive reporting:

**Console Output:**
```
📊 Validation Summary:
  🔴 Hard validation errors: 1
  🟡 Expected range warnings: 11

🔴 Validation Errors:
  year1_return: Validation failed: 10.76 does not satisfy '>= 0 AND <= 1'

🟡 Expected Range Warnings:
  %won: Outside expected range: 0.545 does not meet '>= 0.09 AND <= 0.25'
  hhs: Outside expected range: 13.625 does not meet '>= 1 AND <= 5'
```

**JSON Log Output:**
- Detailed validation results saved in `logs/calculation_log_[record_id].json`
- Includes specific error messages and flagged values
- Structured data for programmatic analysis

### Testing Validation Functions
A test suite is available to verify validation logic:
```sh
python test/test_validation_fix.py
```

This runs comprehensive tests on both hard and soft validation functions with various rule types and edge cases.

---

# AI Reporting V2 - Automated Report Generation System

This project provides an automated report generation system that integrates with Airtable, generates HTML reports, and deploys them to GitHub Pages via Railway webhooks and n8n workflows.

## 🚀 New Features

### Automated Report Generation
- **HTML Report Generation**: Converts calculated data into beautiful HTML reports
- **GitHub Pages Deployment**: Automatically deploys reports to GitHub Pages
- **Webhook Integration**: Railway webhook endpoints for n8n workflow integration
- **Variable Mapping**: Maps Airtable fields to HTML template variables

### System Components
1. **Report Generator** (`scripts/report_generator.py`) - Core report generation and deployment
2. **Webhook Server** (`scripts/webhook_server.py`) - Flask server for n8n integration
3. **Enhanced Calculation Engine** (`scripts/enhanced_calculation_engine.py`) - Integrated calculations + reports
4. **Deployment Configuration** (`scripts/deployment_config.py`) - Setup automation

### Integration Workflow
```
Airtable Trigger → n8n Workflow → Railway Webhook → Report Generation → GitHub Pages
```

## 📋 Quick Start

1. **Setup Environment**:
   ```bash
   python setup.py
   ```

2. **Generate Report Manually**:
   ```bash
   python scripts/enhanced_calculation_engine.py recABC123
   ```

3. **Start Webhook Server**:
   ```bash
   python scripts/webhook_server.py
   ```

## 📚 Documentation

- **[Complete System Documentation](REPORT_GENERATION_SYSTEM.md)** - Full setup and usage guide
- **[GitHub Pages Setup](GITHUB_PAGES_SETUP.md)** - GitHub Pages configuration
- **[n8n Workflow Template](N8N_WORKFLOW_TEMPLATE.md)** - n8n workflow setup

## 🔧 Configuration

The system requires these environment variables:
- `AIRTABLE_API_KEY` - Your Airtable API key
- `AIRTABLE_BASE_ID` - Your Airtable base ID
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPO` - GitHub repository (username/repo-name)
- `WEBHOOK_SECRET` - Secret for webhook security

## 🌐 Webhook Endpoints

- `POST /webhook/generate-report` - Generate full report (async)
- `POST /webhook/generate-report-sync` - Generate full report (sync)
- `POST /webhook/calculation-only` - Run calculations only
- `POST /webhook/deploy-only` - Deploy report only
- `GET /health` - Health check

## 📱 Example Usage

### Manual Report Generation
```bash
# Run calculations and generate report
python scripts/enhanced_calculation_engine.py recABC123

# Generate report only (calculations already done)
python scripts/report_generator.py recABC123
```

### Webhook Usage (from n8n)
```json
{
  "url": "https://your-railway-app.railway.app/webhook/generate-report",
  "method": "POST",
  "headers": {
    "X-Webhook-Secret": "your-webhook-secret",
    "Content-Type": "application/json"
  },
  "body": {
    "report_id": "recABC123"
  }
}
```

## 🎯 Deployment

### Railway Deployment
1. Connect GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy using auto-deploy or manual trigger

### n8n Integration
1. Create Airtable trigger for new records
2. Add HTTP request node pointing to Railway webhook
3. Optional: Add notification nodes for success/failure

## 🧪 Testing

```bash
# Test report generation
python test/test_report_generation.py

# Test specific components
python scripts/report_generator.py recABC123
python scripts/webhook_server.py
```

## 📊 Architecture

The system consists of:
- **Calculation Engine**: Processes Airtable data and performs calculations
- **Report Generator**: Maps data to HTML template and generates reports
- **GitHub Pages**: Hosts the generated HTML reports
- **Railway Webhook**: Provides API endpoints for n8n integration
- **n8n Workflow**: Automates the trigger and execution process

Reports are generated using the existing HTML template (`templates/v2.html`) with dynamic variable substitution based on the field mapping configuration (`field_mapping.json`).

---

## Test Mode for Report Generation

The report generation system includes a **test mode** that allows you to validate reports locally before deployment. This is essential for verifying data mapping and formatting without affecting GitHub Pages or Airtable records.

### Features

- **Local Testing**: Generate reports in `templates/development/` directory
- **Data Validation**: Comprehensive validation of field mappings and data types
- **Validation Reports**: Detailed JSON reports with error/warning analysis
- **Batch Testing**: Test multiple reports at once
- **Safe Environment**: No deployment or Airtable updates in test mode

### Usage

#### Method 1: Direct Script Usage

```bash
# Test a single report
python scripts/report_generator.py <report_id> --test

# Example
python scripts/report_generator.py recABC123 --test
```

#### Method 2: Dedicated Test Script

```bash
# Test a single report
python test_report_generator.py test <report_id>

# Test with verbose output
python test_report_generator.py test <report_id> --verbose

# Test multiple reports in batch
python test_report_generator.py batch <id1> <id2> <id3>

# List files in development directory
python test_report_generator.py list

# Clean development directory
python test_report_generator.py clean
```

### Test Mode Output

1. **HTML Report**: `{client-name}-{date}.html` - Ready to view in browser
2. **Validation Report**: `validation_{client-name}-{date}.json` - Detailed validation results

### Validation Checks

- **Required Fields**: Ensures client_name, hhs, est_auto, est_fire, etc. are present
- **Data Types**: Validates numeric fields contain valid numbers
- **Field Mapping**: Checks all Airtable fields map to template variables
- **Formatting**: Verifies currency, percentage, and date formatting

### Best Practices

1. **Always test first**: Run test mode before production deployment
2. **Check validation**: Review validation results for warnings/errors
3. **Visual inspection**: Open generated HTML files in browser
4. **Batch testing**: Test multiple reports to identify patterns

See `templates/development/README.md` for detailed documentation.

---

## Field Mapping Validation Script
