# Test Files

This folder contains test files for the YTD (Year-to-Date) implementation.

## Files

### test_ytd_logic.py
- Tests the basic YTD calculation logic scenarios
- Covers January, July, and December report scenarios
- Validates the logic for different month ranges

### test_ytd_metadata.py
- Tests the simplified JSON metadata format
- Shows examples of the `hhs_ytd_metadata` field output
- Demonstrates complete data, missing data, and no data scenarios

## Running Tests

From the root directory:

```bash
# Run YTD logic tests
python test/test_ytd_logic.py

# Run YTD metadata tests
python test/test_ytd_metadata.py
```

## Test Scenarios

1. **January Report**: No previous months available
2. **July Report (Complete)**: All previous months have data
3. **July Report (Partial)**: Some months missing data
4. **July Report (No Data)**: No historical data available
