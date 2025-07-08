# YTD Implementation Summary

## Changes Made to calculation_engine.py

### 1. Enhanced CalculationContext Class
- Added `ytd_metadata` dictionary to store YTD calculation details
- Added `report_month` and `report_year` properties extracted from `date_end`
- Handles both datetime objects and ISO string formats

### 2. Added calculate_ytd_value Function
- Calculates Year-to-Date values using only previous full months
- Queries Generated_Reports table for historical data using proper field names (`client`, `year`, `month`, `is_full_month`)
- Returns both the calculated value and simplified metadata
- **NEW**: Fallback logic - uses current month's `hhs` value when no historical data is available
- Handles edge cases (no previous months, missing data, query failures)

### 3. Integrated YTD Calculation into Main Flow
- Added YTD calculation after Level 0 resolution
- Calculates `hhs_ytd` automatically for each report
- Logs results and metadata for transparency
- **NEW**: Provides meaningful YTD values even when historical data is missing

### 4. Enhanced write_to_generated_reports Function  
- **FIXED**: Now properly updates existing records in Generated_Reports table instead of creating duplicates
- Added YTD metadata field to Generated_Reports table:
  - `hhs_ytd_metadata`: Simplified JSON metadata showing each month's value or "missing" status, plus the total YTD value
- **FIXED**: Proper client ID extraction from `client` field (lookup field with record IDs)

## Simplified JSON Format

The `hhs_ytd_metadata` field contains clean, focused JSON:

### Complete Historical Data Example:
```json
{
  "months": {
    "1": 120,
    "2": 110,
    "3": 130,
    "4": 140,
    "5": 125,
    "6": 135
  },
  "ytd_value": 760
}
```

### Missing Historical Data Example:
```json
{
  "months": {
    "1": 120,
    "2": "missing",
    "3": 130,
    "4": 140,
    "5": "missing",
    "6": 135
  },
  "ytd_value": 525
}
```

### **NEW**: No Historical Data - Current Month Fallback Example:
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

### **NEW**: No Previous Months - Current Month Fallback Example (January):
```json
{
  "reason": "No previous months in current year, using current month HHS value",
  "months": {},
  "ytd_value": 15.5,
  "current_month_hhs": 15.5
}
```

## Test Scenarios Covered

1. **January Report**: No previous months → Uses current month's `hhs` value as YTD
2. **July Report (Complete)**: All Jan-Jun months available → Shows all month values and total YTD
3. **July Report (Partial)**: Missing some months → Shows actual values and "missing" for unavailable months
4. **July Report (No Historical Data)**: No historical data available → Uses current month's `hhs` value as YTD fallback
5. **Query Failures**: Database connection issues → Returns "Query failed" status

## Key Features

- **Simplified Output**: Clean JSON with just month values and YTD total
- **Clear Status**: Each month shows either its value or "missing"  
- **Smart Fallback Logic**: Uses current month's `hhs` value when no historical data is available
- **Dynamic Value Retrieval**: Current month's `hhs` is dynamically calculated, not hard-coded
- **Robust Error Handling**: Graceful handling of missing data and query failures
- **Metadata Tracking**: Complete transparency of which months were used and data sources
- **Airtable Integration**: Seamless integration with existing table structure using correct field names
- **Record Management**: Properly updates existing Generated_Reports records instead of creating duplicates
- **Flexible Design**: Easy to extend for additional YTD variables

## Technical Implementation Details

### Field Mapping
- Uses lowercase field names to match Airtable structure: `client`, `year`, `month`, `is_full_month`
- Handles lookup fields properly (extracts values from arrays)
- Converts month names ("January", "February", etc.) to numbers for calculations

### Fallback Logic Flow
1. Check if previous months exist in the current year
2. If no previous months → Use current month's `hhs` value
3. If previous months exist but no historical data found → Use current month's `hhs` value  
4. If historical data found → Calculate traditional YTD sum
5. If current month's `hhs` is also unavailable → Return "No Data"

## Next Steps

1. ✅ **COMPLETED**: Added `hhs_ytd_metadata` field to Generated_Reports table in Airtable
2. ✅ **COMPLETED**: System successfully tested with real data

3. **Future Enhancements**: Consider adding YTD calculations for other variables as needed

## Verification Results

The YTD implementation has been successfully tested and verified:
- ✅ Works with real Generated_Reports data
- ✅ Properly handles field name mappings  
- ✅ Updates existing records correctly
- ✅ Provides meaningful fallback values using current month's `hhs`
- ✅ Generates clean, simplified JSON metadata
- ✅ Integrates seamlessly with existing calculation engine flow
