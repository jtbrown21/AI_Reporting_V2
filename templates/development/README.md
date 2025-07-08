# Test Mode for Report Generation

This directory contains reports generated in test mode for local validation before deployment.

## Overview

The test mode allows you to:
- Generate HTML reports locally without deploying to GitHub Pages
- Validate data mapping and field formatting
- Check for missing or invalid data before publishing
- Review generated reports in a safe environment

## Usage

### Method 1: Using the report generator directly

```bash
# Test a single report
python scripts/report_generator.py <report_id> --test

# Example
python scripts/report_generator.py recABC123 --test
```

### Method 2: Using the dedicated test script

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

## Output Files

When running in test mode, the following files are generated:

1. **HTML Report**: `{client-name}-{date}.html`
   - The actual HTML report that would be deployed
   - Can be opened in a browser for visual inspection

2. **Validation Report**: `validation_{client-name}-{date}.json`
   - Detailed validation results
   - Field mappings and formatting
   - Error and warning messages
   - Raw data from Airtable

## Validation Checks

The test mode performs the following validations:

### Required Fields
- `client_name`: Must be present and non-empty
- `hhs`: Household count (numeric)
- `est_auto`: Estimated auto policies (numeric)
- `est_fire`: Estimated fire policies (numeric)
- `est_annual_commission`: Estimated annual commission (numeric)

### Data Type Validation
- Numeric fields must be valid numbers
- Currency fields are formatted with commas
- Percentage fields are formatted with % symbol
- Date fields are parsed and formatted correctly

### Field Mapping Validation
- Checks if all Airtable fields have corresponding template mappings
- Warns about extra fields not in the mapping
- Validates that template fields receive proper values

## Example Output

```
🧪 Running test mode for report ID: recABC123

📊 Data Validation Results:
Valid: ✓

📋 Field Mappings (15 fields):
  client-name: John Smith Insurance
  new-households: 45
  auto-policies: 67
  fire-policies: 23
  annual-commission: 12,500
  roi: 2.34

🏗️  Generating HTML report for client: John Smith Insurance
✓ Report saved to /path/to/templates/development/John-Smith-Insurance-2025-07-08.html
✓ Validation report saved to /path/to/templates/development/validation_John-Smith-Insurance-2025-07-08.json
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` are set
   - Test mode still needs to fetch data from Airtable

2. **Import Errors**
   - Run the script from the project root directory
   - Ensure all required packages are installed

3. **Permission Errors**
   - Make sure you have write permissions to the templates/development directory

### Validation Failures

If validation fails, check the validation report JSON file for detailed error messages:

```json
{
  "validation_results": {
    "valid": false,
    "errors": [
      "Missing required field: client_name",
      "Invalid numeric value for hhs: 'not a number'"
    ],
    "warnings": [
      "Field 'extra_field' not found in field mapping"
    ]
  }
}
```

## Best Practices

1. **Always test before deploying**
   - Run test mode before using the production deployment
   - Check validation results for any issues

2. **Review generated HTML**
   - Open the HTML file in a browser
   - Verify all data is displaying correctly
   - Check formatting and styling

3. **Batch testing**
   - Test multiple reports at once to identify patterns
   - Use batch mode for comprehensive validation

4. **Clean up regularly**
   - Use the clean command to remove old test files
   - Keep the development directory organized

## Integration with Workflow

1. **Development**: Use test mode to validate new reports
2. **Staging**: Review generated HTML files
3. **Production**: Deploy using regular mode (without --test flag)

This test mode ensures that your reports are properly formatted and contain valid data before they are published to GitHub Pages or shared with clients.
