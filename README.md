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

## Notes
- All scripts require a valid `.env` file with your Airtable API key and base ID.
- Make sure to run the dependency analyzer before running the updater script.
