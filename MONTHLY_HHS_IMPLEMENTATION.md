# Monthly HHS Variables Implementation Summary

## Overview
Implemented special handling for monthly HHS variables (`hhs_jan`, `hhs_feb`, etc.) that are populated from the `hhs_ytd_metadata` field in Airtable, with intelligent handling of missing data and current month values.

## How It Works

### 1. Data Source
- **Primary source**: `hhs_ytd_metadata` field containing YTD calculation results
- **Current month**: Uses the current report's `hhs` value for the report month
- **Default**: Empty string for missing historical data (displays as empty bar in charts)

### 2. YTD Metadata Structure
The system processes this JSON structure from Airtable:
```json
{
  "months": {
    "1": 120,        // January value
    "2": "missing",  // February missing
    "3": 130,        // March value
    "4": "missing",  // April missing
    "5": 125         // May value
  },
  "ytd_value": 375
}
```

### 3. Month Mapping
- Month numbers → field names: `"1"` → `hhs_jan`, `"2"` → `hhs_feb`, etc.
- Supports all 12 months: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec

### 4. Value Processing Logic

#### Historical Months (from YTD metadata)
- **Has value**: Format as integer string (e.g., `120` → `"120"`)
- **Missing**: Set to empty string (`""`) for empty bar chart display
- **Not in metadata**: Default to empty string

#### Current Month (from report date)
- **Always uses current report's `hhs` value**
- **Overrides YTD metadata**: Even if current month is in metadata, use live `hhs` value
- **Formatted**: Applied standard HHS formatting (integer)

## Implementation Details

### Key Method: `_process_monthly_hhs_data()`
```python
def _process_monthly_hhs_data(self, report_data: Dict[str, Any], mapping: Dict[str, str]):
    # 1. Initialize all months as empty
    # 2. Process YTD metadata if available
    # 3. Override current month with live HHS value
    # 4. Handle edge cases (no date, invalid JSON, etc.)
```

### Edge Cases Handled
1. **No YTD metadata**: All months empty except current month
2. **Invalid JSON**: Graceful failure with warning message
3. **No date_end**: Falls back to current system date
4. **Missing current HHS**: Leaves current month empty
5. **String vs Dict metadata**: Handles both JSON string and dict formats

## Testing Results

### Test 1: Complete YTD Metadata
```
Input: June report with Jan-May data, current hhs=45
Output: 
  hhs_jan: "120"
  hhs_feb: "110" 
  hhs_mar: "130"
  hhs_apr: "140"
  hhs_may: "125"
  hhs_jun: "45"  ← Current month value
```

### Test 2: Missing Months
```
Input: July report with some missing months
Output:
  hhs_jan: "120"
  hhs_feb: ""      ← Missing = empty
  hhs_mar: "130"
  hhs_apr: ""      ← Missing = empty
  hhs_may: "125"
  hhs_jun: "135"
  hhs_jul: "80"    ← Current month value
```

### Test 3: No YTD Metadata
```
Input: March report with no YTD metadata
Output:
  hhs_jan: ""      ← All empty
  hhs_feb: ""
  hhs_mar: "55"    ← Only current month
  hhs_apr: ""
  ...
```

### Test 4: JSON String Format
```
Input: YTD metadata as JSON string from Airtable
Output: Correctly parsed and processed
```

## Benefits

1. **Bar Chart Ready**: Empty strings create empty bars, values create filled bars
2. **Current Data**: Always shows live current month data
3. **Historical Accuracy**: Uses actual historical data when available
4. **Graceful Degradation**: Works even with no historical data
5. **Flexible Format**: Handles both string and object JSON formats

## Template Integration

The HTML template can now use these fields directly:
```html
<span data-field="hhs_jan">120</span>
<span data-field="hhs_feb"></span>  <!-- Empty for missing -->
<span data-field="hhs_mar">130</span>
<!-- ... all 12 months supported -->
```

## Future Enhancements

1. **Chart Height Calculation**: Could use max value to normalize bar heights
2. **Missing Data Indicators**: Could show different styling for missing vs zero
3. **Trend Analysis**: Could calculate month-over-month changes
4. **Seasonal Patterns**: Could highlight seasonal trends

This implementation provides a robust foundation for displaying monthly HHS data in bar charts while gracefully handling missing historical data and ensuring current month accuracy.
