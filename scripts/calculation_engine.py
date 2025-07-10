"""
Calculation Engine for Report Generation

This script:
1. Loads raw data from Report_Database
2. Resolves Level 0 values with fallbacks
3. Calculates all derived values using formulas
4. Handles errors and logs everything
5. Writes results to Generated_Reports
"""

import os
import re
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Tuple, Optional, Any, List
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')

# Table names
REPORT_VARIABLES_TABLE = 'Report_Variables'
REPORT_DATABASE_TABLE = 'Client_Reports'
GENERATED_REPORTS_TABLE = 'Generated_Reports'
GLOBAL_VARIABLES_TABLE = 'Global_Variables'
CLIENT_VARIABLES_TABLE = 'Client_Variables'

# Initialize Airtable API
if AIRTABLE_API_KEY is None:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set.")
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)


# Helper to extract value from lookup fields

def extract_lookup_value(field):
    if isinstance(field, list):
        return field[0] if field else None
    return field


class ConversionTracker:
    """
    Track which values have been converted to prevent double conversion
    """
    def __init__(self):
        self.converted_variables = set()
        self.conversion_log = []
    
    def is_converted(self, variable_name):
        """Check if variable has already been converted"""
        return variable_name in self.converted_variables
    
    def mark_converted(self, variable_name, stage, original_value, converted_value):
        """Mark variable as converted and log the conversion"""
        self.converted_variables.add(variable_name)
        log_entry = {
            'variable': variable_name,
            'stage': stage,
            'original': original_value,
            'converted': converted_value,
            'timestamp': datetime.now().isoformat()
        }
        self.conversion_log.append(log_entry)
        print(f"CONVERSION: {variable_name} at {stage}: {original_value} → {converted_value}")
    
    def reset_for_new_calculation(self):
        """Reset tracker for new calculation context"""
        self.converted_variables.clear()
        self.conversion_log.clear()


def safe_percentage_conversion(value, variable_name, current_stage, tracker):
    """
    Convert percentage to decimal ONLY if not already converted
    Returns: (converted_value, was_converted_bool)
    """
    if value is None:
        return None, False
    
    # Check if already converted
    if tracker.is_converted(variable_name):
        print(f"SKIP: {variable_name} at {current_stage} - already converted")
        return float(value), False
    
    original_value = value
    
    # Handle string percentages (e.g., "25%")
    if isinstance(value, str) and value.strip().endswith('%'):
        converted_value = float(value.strip()[:-1]) / 100
        tracker.mark_converted(variable_name, current_stage, original_value, converted_value)
        return converted_value, True
    
    # Handle numeric values that need conversion
    try:
        numeric_value = float(value)
        # Fixed logic: Convert if value appears to be in percentage format
        # Values between 0 and 1 are assumed to already be in decimal format
        # Values >= 1 are assumed to be in percentage format (1% = 1, 150% = 150)
        if numeric_value >= 1:
            converted_value = numeric_value / 100
            tracker.mark_converted(variable_name, current_stage, original_value, converted_value)
            return converted_value, True
        else:
            # Value is already in decimal format (0.25 for 25%)
            # BUT: check if it's exactly 1.0 (could be 100%)
            if numeric_value == 1.0:
                # Need context to decide - for now, assume it's already converted
                print(f"AMBIGUOUS: {variable_name} at {current_stage}: value=1.0 (could be 100% or already converted)")
            print(f"ALREADY_DECIMAL: {variable_name} at {current_stage}: {value}")
            return numeric_value, False
    except (ValueError, TypeError):
        print(f"CONVERSION_ERROR: {variable_name} at {current_stage}: {value}")
        return value, False


def parse_numeric_value(value):
    """
    Parse a value to numeric, handling currency formats with commas and dollar signs
    
    Args:
        value: The value to parse (can be string, int, float)
    
    Returns:
        float: The parsed numeric value
    
    Raises:
        ValueError: If the value cannot be parsed as a number
    """
    if value is None:
        raise ValueError("Value is None")
    
    # If already a number, return as float
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and clean it
    str_value = str(value).strip()
    
    # Remove common currency symbols and formatting
    str_value = str_value.replace('$', '').replace(',', '').replace(' ', '')
    
    # Handle percentage values
    if str_value.endswith('%'):
        str_value = str_value[:-1]
        return float(str_value) / 100.0
    
    # Try to convert to float
    try:
        return float(str_value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid number for comparison")


class CalculationContext:
    """Holds all data needed during calculation"""
    def __init__(self, client_id: str, report_record: Any):
        self.client_id = client_id
        self.report_record = report_record
        self.date_start = report_record['fields'].get('date_start')
        self.date_end = report_record['fields'].get('date_end')
        self.raw_data = report_record['fields']
        self.calculated_values = {}
        self.fallback_log = []
        self.calculation_log = []
        self.errors = []
        self.warnings = []
        self.ytd_metadata = {}
        self.validation_flags = []
        self.expected_flags = []
        self.conversion_tracker = ConversionTracker()  # Add conversion tracker
        
        # Extract client_record_id for YTD queries
        client_record_id = report_record['fields'].get('client_record_id')
        if isinstance(client_record_id, list):
            self.client_record_id = client_record_id[0] if client_record_id else None
        else:
            self.client_record_id = client_record_id
        
        # Extract report month and year from date_end
        date_end = self.date_end
        if isinstance(date_end, list):
            date_end = date_end[0] if date_end else None
        if isinstance(date_end, datetime):
            self.report_month = date_end.month
            self.report_year = date_end.year
        elif isinstance(date_end, str) and date_end:
            dt_date_end = datetime.fromisoformat(date_end)
            self.report_month = dt_date_end.month
            self.report_year = dt_date_end.year
        else:
            self.report_month = None
            self.report_year = None
        
    def add_value(self, variable: str, value: Any, source: str = "calculated"):
        """Add a calculated or resolved value"""
        self.calculated_values[variable] = value
        if source != "calculated":
            self.fallback_log.append({
                'variable': variable,
                'value': value,
                'source': source,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_value(self, variable: str) -> Optional[Any]:
        """Get a value from either calculated or raw data"""
        if variable in self.calculated_values:
            return self.calculated_values[variable]
        # Always extract lookup value for known lookup fields
        lookup_fields = [
            'quote_starts', 'sms_clicks', 'phone_clicks', 'total_leads', 'conversions', 'cost',
            'search_impression_share', 'search_lost_IS_budget'
        ]
        raw = self.raw_data.get(variable)
        if variable in lookup_fields:
            return extract_lookup_value(raw)
        return raw
    
    def get_all_values(self) -> Dict[str, Any]:
        """Get all values for formula evaluation, applying lookup extraction to known fields"""
        all_values = {}
        all_values.update(self.raw_data)
        all_values.update(self.calculated_values)
        # Ensure all known lookup fields are scalars
        lookup_fields = [
            'quote_starts', 'sms_clicks', 'phone_clicks', 'total_leads', 'conversions', 'cost',
            'search_impression_share', 'search_lost_IS_budget'
        ]
        for field in lookup_fields:
            if field in all_values:
                all_values[field] = extract_lookup_value(all_values[field])
        return all_values


def load_report_variables() -> Dict[str, dict]:
    """Load all report variables and their metadata"""
    print("DEBUG: Entering load_report_variables()")
    table = base.table(REPORT_VARIABLES_TABLE)
    try:
        print("DEBUG: Fetching all records from Report_Variables...")
        records = table.all()
        print(f"DEBUG: Retrieved {len(records)} records.")
    except Exception as e:
        print(f"ERROR: Failed to fetch records from Report_Variables: {e}")
        raise
    variables = {}
    for record in records:
        var_id = record['fields'].get('Variable_ID')
        if var_id:
            variables[var_id] = {
                'record_id': record['id'],
                'fields': record['fields'],
                'formula': record['fields'].get('Formula', ''),
                'fallback_1': record['fields'].get('Fallback 1'),
                'fallback_2': record['fields'].get('Fallback 2'),
                'previous_period_max': int(record['fields'].get('Previous_Period_Max', '6') or 0),
                'data_type': record['fields'].get('Data_Type', 'number'),
                'calculation_depth': record['fields'].get('Calculation Depth', 'Level 0')
            }
    
    return variables


def load_global_variables() -> Dict[str, Any]:
    """Load global default values"""
    table = base.table(GLOBAL_VARIABLES_TABLE)
    records = table.all()
    print(f"DEBUG: Raw records from Global_Variables: {json.dumps(records, indent=2, default=str)[:1000]}")  # Print first 1000 chars
    globals_dict = {}
    for record in records:
        var_name = record['fields'].get('Variable_ID')
        value = record['fields'].get('Value')
        data_type = record['fields'].get('Data_Type', 'number')  # Default to number if missing
        if var_name and value is not None:
            # Remove '_global' suffix if present
            clean_name = var_name.replace('_global', '')
            # Convert value based on data_type
            if data_type in ('number', 'currency', 'percentage'):
                try:
                    globals_dict[clean_name] = float(value)
                except Exception:
                    globals_dict[clean_name] = value  # fallback to raw if conversion fails
            elif data_type == 'text':
                globals_dict[clean_name] = str(value)
            else:
                globals_dict[clean_name] = value
    
    return globals_dict


def find_previous_period_value(
    variable: str, 
    client_id: str, 
    current_date_end: datetime, 
    max_months: int,
    current_date_start: Optional[datetime] = None
) -> Optional[Any]:
    """Find value from previous report within max_months"""
    table = base.table(GENERATED_REPORTS_TABLE)
    
    # Calculate date range - go back max_months * 30 days from current date
    min_date = current_date_end - timedelta(days=max_months * 30)
    
    # Normalize client_id to string for comparison
    if isinstance(client_id, list):
        client_id = client_id[0] if client_id else ""
    if client_id is None:
        client_id = ""
    
    # Use date_start if available, otherwise fall back to date_end
    comparison_date = current_date_start if current_date_start else current_date_end
    
    try:
        # Get all records without formula filtering (to avoid lookup field issues)
        all_records = table.all(fields=['client', 'date_end', 'date_start', 'is_full_month', variable])
        
        # Filter in Python for better lookup field handling
        matching_records = []
        for record in all_records:
            fields = record['fields']
            
            # Check client match (handle both single values and arrays)
            client_field = fields.get('client')
            client_match = False
            if client_field:
                if isinstance(client_field, list):
                    client_match = client_id in client_field
                else:
                    client_match = client_field == client_id
            
            if not client_match:
                continue
            
            # Check is_full_month
            is_full_month = fields.get('is_full_month')
            if isinstance(is_full_month, list):
                is_full_month = is_full_month[0] if is_full_month else False
            if not is_full_month:
                continue
            
            # Check date_end is within range
            date_end = fields.get('date_end')
            if isinstance(date_end, list):
                date_end = date_end[0] if date_end else None
            if date_end:
                if isinstance(date_end, str):
                    date_end_dt = datetime.fromisoformat(date_end)
                else:
                    date_end_dt = date_end
                
                # Must be before comparison date and after min_date
                if date_end_dt < comparison_date and date_end_dt > min_date:
                    matching_records.append((record, date_end_dt))
        
        # Sort by date_end descending (most recent first)
        matching_records.sort(key=lambda x: x[1], reverse=True)
        
        # Find first record with the requested variable
        for record, _ in matching_records:
            if variable in record['fields'] and record['fields'][variable] is not None:
                return record['fields'][variable]
                
    except Exception as e:
        print(f"Error searching previous periods: {e}")
    
    return None


def apply_fallback(
    fallback_type: str,
    variable: str,
    context: CalculationContext,
    global_vars: Dict[str, Any],
    max_periods: int = 6
) -> Tuple[Optional[Any], str]:
    """Apply a single fallback strategy"""
    
    if not fallback_type:
        return None, "no_fallback"
    
    if fallback_type == "0":
        return 0, "zero_fallback"
    
    elif fallback_type == "previous_period":
        # Safely handle lookup field for date_end and date_start
        date_end = context.date_end
        if isinstance(date_end, list):
            date_end = date_end[0] if date_end else None
        if isinstance(date_end, datetime):
            dt_date_end = date_end
        elif isinstance(date_end, str) and date_end:
            dt_date_end = datetime.fromisoformat(date_end)
        else:
            return None, "invalid_date_end"
        
        # Get date_start for improved filtering
        date_start = context.date_start
        if isinstance(date_start, list):
            date_start = date_start[0] if date_start else None
        dt_date_start = None
        if date_start:
            if isinstance(date_start, datetime):
                dt_date_start = date_start
            elif isinstance(date_start, str) and date_start:
                dt_date_start = datetime.fromisoformat(date_start)
        
        value = find_previous_period_value(
            variable,
            context.client_id,
            dt_date_end,
            max_periods,
            dt_date_start
        )
        if value is not None:
            return value, f"previous_period({max_periods}mo)"
        
    elif fallback_type == "global_default":
        if variable in global_vars:
            return global_vars[variable], "global_default"
    
    elif fallback_type == "calculation":
        # Try to calculate using the variable's formula
        return None, "calculation_needed"  # Signal that calculation should be attempted
    
    return None, f"fallback_failed({fallback_type})"


def resolve_value(
    variable: str,
    context: CalculationContext,
    var_config: dict,
    global_vars: Dict[str, Any]
) -> Optional[Any]:
    """Resolve a value using fallback chain if needed"""
    
    # Special logic for client_static variables - check before fallbacks AND before existing values
    source_type = var_config.get('fields', {}).get('Source_Type', '').lower()
    if source_type == 'client_static':
        # Look up value in Client_Variables for this client
        client_id = context.client_id
        client_table = base.table(CLIENT_VARIABLES_TABLE)
        try:
            client_record = client_table.get(client_id)
            if client_record and variable in client_record['fields']:
                client_value = client_record['fields'][variable]
                # Convert value to correct type using Data_Type from Report_Variables
                data_type = var_config.get('fields', {}).get('Data_Type', 'number')
                if data_type in ('number', 'currency', 'percentage'):
                    try:
                        if data_type == 'percentage':
                            client_value, _ = safe_percentage_conversion(
                                client_value, variable, 'resolve_value', context.conversion_tracker
                            )
                        else:
                            client_value = float(client_value)
                    except Exception:
                        pass  # fallback to raw if conversion fails
                elif data_type == 'text':
                    client_value = str(client_value)
                # Add to context and return
                context.add_value(variable, client_value, 'client_static')
                return client_value
        except Exception as e:
            print(f"Error fetching client_static value for {variable}: {e}")
        # No value found in Client_Variables, proceed to fallbacks
    
    # First check if we already have the value (only for non-client_static variables)
    existing_value = context.get_value(variable)
    if existing_value is not None:
        return existing_value

    # Always define max_periods before using in fallbacks
    max_periods = var_config.get('previous_period_max', 0)
    # Ensure it's an int
    try:
        max_periods = int(max_periods)
    except Exception:
        max_periods = 0

    # Try Fallback 1
    if var_config.get('fallback_1'):
        value, source = apply_fallback(
            var_config['fallback_1'],
            variable,
            context,
            global_vars,
            max_periods
        )
        if source == "calculation_needed":
            # Try to calculate using formula
            formula = var_config.get('formula', '')
            if formula:
                # Get all available values for formula evaluation
                all_values = context.get_all_values()
                # Build variable_types dict for this formula
                variable_types = {k: var_config.get('fields', {}).get('Data_Type', 'number') for k in re.findall(r'\{([^}]+)\}', formula)}
                result, error, expr, var_values = evaluate_formula(formula, all_values, variable, variable_types, context.calculated_values, context)
                if not error and result is not None:
                    context.add_value(variable, result, "calculated_fallback")
                    return result
            # If calculation failed, continue to next fallback
        elif value is not None:
            # Apply data type conversion if needed
            data_type = var_config.get('fields', {}).get('Data_Type', 'number')
            if data_type == 'percentage':
                try:
                    value, _ = safe_percentage_conversion(
                        value, variable, 'apply_fallback', context.conversion_tracker
                    )
                except (ValueError, TypeError):
                    pass  # If conversion fails, use original value
            context.add_value(variable, value, source)
            return value
    
    # Try Fallback 2
    if var_config.get('fallback_2'):
        value, source = apply_fallback(
            var_config['fallback_2'],
            variable,
            context,
            global_vars,
            max_periods
        )
        if source == "calculation_needed":
            # Try to calculate using formula
            formula = var_config.get('formula', '')
            if formula:
                # Get all available values for formula evaluation
                all_values = context.get_all_values()
                # Build variable_types dict for this formula
                variable_types = {k: var_config.get('fields', {}).get('Data_Type', 'number') for k in re.findall(r'\{([^}]+)\}', formula)}
                result, error, expr, var_values = evaluate_formula(formula, all_values, variable, variable_types, context.calculated_values, context)
                if not error and result is not None:
                    context.add_value(variable, result, "calculated_fallback")
                    return result
            # If calculation failed, continue
        elif value is not None:
            # Apply data type conversion if needed
            data_type = var_config.get('fields', {}).get('Data_Type', 'number')
            if data_type == 'percentage':
                try:
                    value, _ = safe_percentage_conversion(
                        value, variable, 'apply_fallback', context.conversion_tracker
                    )
                except (ValueError, TypeError):
                    pass  # If conversion fails, use original value
            context.add_value(variable, value, source)
            return value
    
    # No value found
    return None


def evaluate_formula(
    formula: str,
    values: Dict[str, Any],
    variable_name: Optional[str] = None,
    variable_types: Optional[Dict[str, str]] = None,
    calculated_values: Optional[Dict[str, Any]] = None,
    context: Optional[CalculationContext] = None  # Add context parameter
) -> Tuple[Optional[float], Optional[str], Optional[str], Optional[List[str]]]:
    """
    Safely evaluate a formula like '{hhs} x {autos_per_hh}',
    returning (result, error_message, evaluated_expression, variable_values_list)
    """
    if not formula:
        return None, "No formula provided", None, None
    try:
        expression = formula
        variables_used = []
        var_values = []
        for var_match in re.findall(r'\{([^}]+)\}', formula):
            if var_match not in values or values[var_match] is None:
                return None, f"Missing required variable: {var_match}", None, None
            value = values[var_match]
            if isinstance(value, list):
                value = value[0] if value else None
            if variable_types and variable_types.get(var_match) == 'percentage':
                if context and hasattr(context, 'conversion_tracker'):
                    value, _ = safe_percentage_conversion(
                        value, var_match, 'evaluate_formula', context.conversion_tracker
                    )
                else:
                    # Fallback to original logic if no context
                    print(f"WARNING: No conversion tracker available for {var_match}")
                    try:
                        if isinstance(value, str):
                            value_clean = value.replace('%', '').replace(',', '').strip()
                            value = float(value_clean) / 100 if value_clean else None
                        elif value is not None:
                            value = float(value) / 100
                    except (ValueError, TypeError):
                        pass
            if isinstance(value, str):
                value_clean = value.replace(',', '').strip()
                try:
                    value = float(value_clean) if value_clean else None
                except Exception:
                    pass
            variables_used.append(f"{var_match}={value}")
            var_values.append(f"{var_match}={value}")
            if isinstance(value, (int, float, Decimal)):
                expression = expression.replace(f'{{{var_match}}}', str(value))
            else:
                return None, f"Non-numeric value for {var_match}: {value}", None, None
        expression = expression.replace(' x ', ' * ').replace(' X ', ' * ')
        expression = expression.strip()
        if expression.startswith('='):
            expression = expression[1:].strip()
        if not re.match(r'^[0-9\.\+\-\*\/\(\)\s]+$', expression):
            return None, f"Invalid characters in formula: {expression}", None, None
        try:
            result = eval(expression)
            print(f"  {variable_name}: {formula} → {expression} = {result}")
            print(f"    Variables: {', '.join(variables_used)}")
            return float(result), None, expression, var_values
        except ZeroDivisionError:
            return 0, f"Division by zero in formula: {formula}", expression, var_values
        except Exception as e:
            return None, f"Evaluation error: {str(e)}", expression, var_values
    except Exception as e:
        return None, f"Formula parsing error: {str(e)}", None, None


def calculate_ytd_value(context, base_variable='hhs'):
    """
    Calculate YTD for a variable using only previous full months
    Returns: (value, metadata_dict)
    
    Improved version with better error handling and debugging
    """
    
    print(f"\n=== YTD CALCULATION DEBUG ===")
    print(f"Base variable: {base_variable}")
    print(f"Context client_id: {context.client_id}")
    print(f"Context client_record_id: {context.client_record_id}")
    print(f"Context report_month: {context.report_month}")
    print(f"Context report_year: {context.report_year}")
    print(f"Context date_start: {context.date_start}")
    print(f"Context date_end: {context.date_end}")
    
    # Only calculate for previous complete months (not current)
    previous_months = list(range(1, context.report_month)) if context.report_month else []
    
    if not previous_months:
        # For January or when no previous months exist, use current month's HHS value
        current_hhs = context.get_value('hhs')
        print(f"No previous months found. Current HHS: {current_hhs}")
        if current_hhs is not None:
            return current_hhs, {
                'reason': 'No previous months in current year, using current month HHS value',
                'months': {},
                'ytd_value': current_hhs,
                'current_month_hhs': current_hhs
            }
        else:
            return "No Data", {
                'reason': 'No previous months and no current month HHS value available',
                'months': {},
                'ytd_value': 0
            }
    
    print(f"Looking for previous months: {previous_months}")
    
    # Get all records from Generated_Reports table without complex filtering
    # We'll filter in Python for better control and debugging
    table = base.table(GENERATED_REPORTS_TABLE)
    
    try:
        print("Fetching all Generated_Reports records...")
        all_records = table.all(fields=[
            'client', 'client_record_id', 'month', 'year', 'is_full_month', 
            'date_start', 'date_end', base_variable
        ])
        print(f"Retrieved {len(all_records)} total records")
        
        # Filter records step by step with detailed logging
        matching_records = []
        
        for i, record in enumerate(all_records):
            fields = record['fields']
            record_id = record['id']
            
            # Debug first few records
            if i < 5:
                print(f"\nRecord {i+1} ({record_id}):")
                print(f"  client: {fields.get('client')}")
                print(f"  client_record_id: {fields.get('client_record_id')}")
                print(f"  month: {fields.get('month')}")
                print(f"  year: {fields.get('year')}")
                print(f"  is_full_month: {fields.get('is_full_month')}")
                print(f"  {base_variable}: {fields.get(base_variable)}")
            
            # Step 1: Check client match
            client_match = False
            client_field = fields.get('client')
            client_record_id_field = fields.get('client_record_id')
            
            # Try multiple ways to match client
            if context.client_record_id:
                # Method 1: Direct client_record_id match
                if client_record_id_field:
                    if isinstance(client_record_id_field, list):
                        client_match = context.client_record_id in client_record_id_field
                    else:
                        client_match = client_record_id_field == context.client_record_id
                
                # Method 2: client field match (fallback)
                if not client_match and client_field:
                    if isinstance(client_field, list):
                        client_match = context.client_record_id in client_field
                    else:
                        client_match = client_field == context.client_record_id
            
            # Method 3: Use context.client_id as fallback
            if not client_match and context.client_id and client_field:
                if isinstance(client_field, list):
                    client_match = context.client_id in client_field
                else:
                    client_match = client_field == context.client_id
            
            if not client_match:
                continue
            
            # Step 2: Check year match
            year_match = False
            year_field = fields.get('year')
            if year_field:
                if isinstance(year_field, list):
                    year_match = str(context.report_year) in [str(y) for y in year_field]
                else:
                    year_match = str(year_field) == str(context.report_year)
            
            if not year_match:
                continue
            
            # Step 3: Check is_full_month
            is_full_month = fields.get('is_full_month')
            if isinstance(is_full_month, list):
                is_full_month = is_full_month[0] if is_full_month else False
            if not is_full_month:
                continue
            
            # Step 4: Check month is in previous months
            month_field = fields.get('month')
            month_num = None
            
            if month_field:
                if isinstance(month_field, list):
                    month_field = month_field[0] if month_field else None
                
                # Convert month name to number if needed
                if isinstance(month_field, str):
                    month_names = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }
                    month_num = month_names.get(month_field)
                else:
                    try:
                        month_num = int(month_field) if month_field is not None else None
                    except (ValueError, TypeError):
                        continue
            
            if month_num not in previous_months:
                continue
            
            # Step 5: Check if variable has a value
            variable_value = fields.get(base_variable)
            if variable_value is None:
                continue
            
            # Handle lookup fields
            if isinstance(variable_value, list):
                variable_value = variable_value[0] if variable_value else None
            
            if variable_value is None:
                continue
            
            # Record passed all filters
            matching_records.append({
                'record_id': record_id,
                'month': month_num,
                'value': variable_value,
                'fields': fields
            })
        
        print(f"\nFound {len(matching_records)} matching records after filtering")
        
        # Build month data
        months_with_data = {}
        for record in matching_records:
            month = record['month']
            value = record['value']
            print(f"  Month {month}: {value}")
            
            # Convert value to numeric if needed
            try:
                if isinstance(value, str):
                    value = float(value.replace(',', '').replace('$', ''))
                else:
                    value = float(value)
                months_with_data[month] = value
            except (ValueError, TypeError):
                print(f"  Warning: Could not convert value '{value}' to numeric for month {month}")
                continue
        
        print(f"\nMonths with valid data: {months_with_data}")
        
        # Check if we have any data
        if not months_with_data:
            # Fallback: Use current month's HHS value as YTD when no historical data available
            current_hhs = context.get_value('hhs')
            print(f"No historical data found. Current HHS: {current_hhs}")
            
            if current_hhs is not None:
                # Still show which months were checked but had no data
                month_details = {}
                for month in previous_months:
                    month_details[str(month)] = "missing"
                
                return current_hhs, {
                    'reason': 'No historical data found, using current month HHS value',
                    'months': month_details,
                    'ytd_value': current_hhs,
                    'current_month_hhs': current_hhs
                }
            else:
                # No historical data AND no current HHS value
                month_details = {}
                for month in previous_months:
                    month_details[str(month)] = "missing"
                
                return "No Data", {
                    'reason': 'No historical data and no current month HHS value available',
                    'months': month_details,
                    'ytd_value': 0
                }
        
        # Calculate YTD - sum previous months plus current month
        previous_months_total = sum(months_with_data.values())
        print(f"Previous months total: {previous_months_total}")
        
        # Add current month's HHS value
        current_hhs = context.get_value('hhs')
        print(f"Current month HHS: {current_hhs}")
        
        if current_hhs is not None:
            try:
                # Convert current HHS to numeric if needed
                if isinstance(current_hhs, str):
                    current_hhs_numeric = float(current_hhs.replace(',', '').replace('$', ''))
                else:
                    current_hhs_numeric = float(current_hhs)
                
                ytd_total = previous_months_total + current_hhs_numeric
                print(f"YTD Total (previous + current): {ytd_total}")
            except (ValueError, TypeError):
                print(f"Warning: Could not convert current HHS '{current_hhs}' to numeric, using only previous months")
                ytd_total = previous_months_total
        else:
            print("Warning: No current month HHS value available, using only previous months")
            ytd_total = previous_months_total
        
        # Build simplified metadata - show each month with its value or "missing"
        month_details = {}
        for month in previous_months:
            if month in months_with_data:
                month_details[str(month)] = months_with_data[month]
            else:
                month_details[str(month)] = "missing"
        
        # Add current month to metadata
        if current_hhs is not None:
            month_details[str(context.report_month)] = current_hhs
        
        metadata = {
            'months': month_details,
            'ytd_value': ytd_total,
            'debug_info': {
                'total_records_checked': len(all_records),
                'matching_records_found': len(matching_records),
                'months_with_data': list(months_with_data.keys()),
                'client_matching_method': 'client_record_id' if context.client_record_id else 'client_id'
            }
        }
        
        print(f"=== YTD CALCULATION COMPLETE ===\n")
        return ytd_total, metadata
        
    except Exception as e:
        print(f"ERROR in YTD calculation: {e}")
        import traceback
        traceback.print_exc()
        
        context.errors.append(f"Error in YTD calculation: {e}")
        return "No Data", {
            'reason': f'YTD calculation failed: {str(e)}',
            'months': {},
            'ytd_value': 0
        }


def calculate_all_variables(
    context: CalculationContext,
    dependency_analysis: dict,
    report_variables: Dict[str, dict],
    global_vars: Dict[str, Any]
) -> bool:
    """Main calculation engine"""
    
    # CRITICAL: Reset tracker at start of new calculation
    context.conversion_tracker.reset_for_new_calculation()
    
    print("\n" + "="*70)
    print("STARTING CALCULATION ENGINE")
    print("="*70)
    
    # Get calculation order from dependency analysis
    calculation_order = dependency_analysis.get('calculation_order', {})
    
    # First, resolve all Level 0 variables with fallbacks
    print("\nResolving Level 0 variables...")
    level_0_vars = calculation_order.get('level_0', [])
    
    for var in level_0_vars:
        if var in report_variables:
            value = resolve_value(var, context, report_variables[var], global_vars)
            if value is not None:
                # Don't override the source - resolve_value already added it to context with correct source
                print(f"  ✓ Resolved {var}: {value}")
            else:
                # Check if this is a critical variable
                context.warnings.append(f"Level 0 variable '{var}' has no value")
                print(f"  ⚠️ {var}: No value found")

    # Calculate levels 1-5 in order
    for level in range(1, 6):
        level_vars = calculation_order.get(f'level_{level}', [])
        
        if not level_vars:
            continue
            
        print(f"\nCalculating Level {level} ({len(level_vars)} variables)...")
        
        for var in level_vars:
            if var not in report_variables:
                context.errors.append(f"Variable '{var}' not found in Report_Variables")
                continue
            
            var_config = report_variables[var]
            source_type = var_config['fields'].get('Source_Type', '').lower()
            formula = var_config.get('formula', '')

            # Only require a formula if Source_Type is not 'client_historical'
            if source_type != 'client_historical' and not formula:
                context.errors.append(f"No formula for calculated variable '{var}'")
                continue

            # If Source_Type is 'client_historical', skip formula and let special logic handle it
            if source_type == 'client_historical':
                # YTD or historical logic handled elsewhere (after level 3, etc.)
                continue

            # Get all available values for formula evaluation
            all_values = context.get_all_values()
            
            # Build variable_types dict for this formula
            variable_types = {k: report_variables[k]['fields'].get('Data_Type', 'number') for k in re.findall(r'\{([^}]+)\}', formula) if k in report_variables}
            # Evaluate the formula with type info
            result, error, expr, var_values = evaluate_formula(formula, all_values, var, variable_types, context.calculated_values, context)
            if error:
                context.errors.append(f"Error calculating {var}: {error}")
                # Try fallbacks for calculated variables
                fallback_value = resolve_value(var, context, var_config, global_vars)
                if fallback_value is not None:
                    context.add_value(var, fallback_value, "fallback_after_error")
            else:
                context.add_value(var, result, "calculated")
                context.calculation_log.append({
                    'variable': var,
                    'formula': formula,
                    'result': result,
                    'level': level,
                    'expression': expr,
                    'variables': var_values
                })
        
        # After level 3, calculate YTD values since 'hhs' is now available
        if level == 3:
            print("\nCalculating YTD values...")
            ytd_value, ytd_metadata = calculate_ytd_value(context, 'hhs')

            if ytd_value == "No Data":
                context.add_value('hhs_ytd', None, 'no_data')
                context.warnings.append(f"hhs_ytd: {ytd_metadata.get('reason', 'No data available')}")
            else:
                context.add_value('hhs_ytd', ytd_value, 'calculated_ytd')
                context.calculation_log.append({
                    'variable': 'hhs_ytd',
                    'type': 'ytd_calculation',
                    'result': ytd_value,
                    'metadata': ytd_metadata
                })

            # Store YTD metadata for transparency
            context.ytd_metadata = {'hhs_ytd': ytd_metadata}
    
    # Validate all calculated values
    print(f"\nValidating calculated values...")
    validate_all_calculated_values(context, report_variables)
    
    print(f"\n✓ Calculation complete")
    print(f"  Calculated: {len(context.calculated_values)} values")
    print(f"  Errors: {len(context.errors)}")
    print(f"  Warnings: {len(context.warnings)}")
    
    return len(context.errors) == 0


def write_to_generated_reports(
    context: CalculationContext,
    report_variables: Dict[str, dict],
    source_table: Optional[str] = None
) -> Optional[str]:
    """Write calculation results to Generated_Reports table"""
    
    table = base.table(GENERATED_REPORTS_TABLE)
    
    # Prepare all fields for the report (only include fields that exist in the table)
    report_fields = {}
    
    # Handle client_report field based on source table
    if source_table == GENERATED_REPORTS_TABLE:
        # For records already in Generated_Reports, get the existing client_report link
        existing_client_report = context.report_record['fields'].get('client_report')
        if existing_client_report:
            report_fields['client_report'] = existing_client_report
            print(f"DEBUG: Using existing client_report link: {existing_client_report}")
        else:
            print("DEBUG: No existing client_report link found")
        # If no existing link, don't include the field (it will remain unchanged)
    else:
        # For records from Client_Reports, link to the source record
        report_fields['client_report'] = [context.report_record['id']]
        print(f"DEBUG: Creating new client_report link: {[context.report_record['id']]}")
    
    # Add all calculated values that are defined in Report_Variables
    all_values = context.get_all_values()
    print(f"\nProcessing {len(all_values)} values for Generated_Reports...")
    print(f"DEBUG: average_premium_per_household in all_values: {'average_premium_per_household' in all_values}")
    if 'average_premium_per_household' in all_values:
        print(f"DEBUG: average_premium_per_household value: {all_values['average_premium_per_household']}")
        print(f"DEBUG: average_premium_per_household type: {type(all_values['average_premium_per_household'])}")
        print(f"DEBUG: average_premium_per_household in report_variables: {'average_premium_per_household' in report_variables}")
    
    for var_name, value in all_values.items():
        if var_name == 'average_premium_per_household':
            print(f"DEBUG: Processing average_premium_per_household specifically...")
        if var_name in report_variables:
            # Skip variables where Source_Detail contains 'My SF Domain Report'
            source_detail = report_variables[var_name]['fields'].get('Source_Detail', [])
            if isinstance(source_detail, str):
                source_detail = [source_detail]
            if 'My SF Domain Report' in source_detail:
                print(f"  Skipping {var_name}: SF Domain Report")
                continue
            data_type = report_variables[var_name]['fields'].get('Data_Type', 'number')
            if isinstance(data_type, list):
                data_type = data_type[0] if data_type else 'number'
            if value is not None:
                if isinstance(value, list):
                    value = value[0] if value else None
            if value is not None:
                if data_type == 'currency' or data_type == 'number':
                    try:
                        numeric_value = parse_numeric_value(value)
                        
                        # For currency fields, ensure proper formatting
                        if data_type == 'currency':
                            # Round to 2 decimal places for currency
                            numeric_value = round(float(numeric_value), 2)
                            print(f"  {var_name}: {value} → {numeric_value} (currency field, rounded to 2 decimals)")
                        else:
                            print(f"  {var_name}: {value} → {numeric_value} (number field)")
                            
                        report_fields[var_name] = numeric_value
                    except Exception as e:
                        report_fields[var_name] = None
                        print(f"  {var_name}: {value} → ERROR ({data_type} conversion failed): {e}")
                elif data_type == 'percentage':
                    original = value
                    try:
                        # Use safe conversion to prevent double conversion
                        converted, was_converted = safe_percentage_conversion(
                            value, var_name, 'write_to_generated_reports', context.conversion_tracker
                        )
                        report_fields[var_name] = converted
                        if not was_converted:
                            print(f"DEBUG: {var_name} already in correct format: {value}")
                    except Exception as e:
                        print(f"DEBUG: Error converting {var_name}: {e}")
                        report_fields[var_name] = value
                elif data_type == 'text':
                    report_fields[var_name] = str(value)
                    print(f"  {var_name}: {value} → {str(value)} (text)")
                else:
                    report_fields[var_name] = value
                    print(f"  {var_name}: {value} → {value} (other/{data_type})")
            else:
                print(f"  Skipping {var_name}: value is None")
        else:
            print(f"  Skipping {var_name}: not in report_variables")
    
    # Note: Metadata fields like 'Fallback Details', 'Validation Warnings', etc.
    # are commented out because they may not exist in the actual Airtable schema
    
    # Add fallback details
    if context.fallback_log:
        fallback_summary = json.dumps(context.fallback_log, indent=2)
        report_fields['Fallback Details'] = fallback_summary[:50000]  # Airtable text limit
    
    # Add any warnings
    if context.warnings:
        report_fields['Validation Warnings'] = '\n'.join(context.warnings)
    # Format calculation log as a comprehensive report for Airtable
    def format_calc_log(log):
        output = []
        
        # Group variables by level
        level_vars = {}
        for entry in log:
            level = entry.get('level')
            if level is not None:
                if level not in level_vars:
                    level_vars[level] = []
                level_vars[level].append(entry)
        
        # Process each level
        for level in sorted(level_vars.keys()):
            entries = level_vars[level]
            output.append(f"**LEVEL {level} CALCULATIONS ({len(entries)} variables):**")
            output.append("")
            
            for entry in entries:
                var = entry.get('variable')
                formula = entry.get('formula', '')
                result = entry.get('result')
                expr = entry.get('expression', '')
                variables = entry.get('variables', [])
                
                # Format the result value
                if isinstance(result, float):
                    if result > 100:
                        result_str = f"{result:,.2f}"
                    elif result > 1:
                        result_str = f"{result:.2f}"
                    else:
                        result_str = f"{result:.4f}"
                else:
                    result_str = str(result)
                
                output.append(f"✓ **{var}** = {result_str}")
                
                # Show formula and calculation
                if formula and expr:
                    output.append(f"  Formula: {formula}")
                    output.append(f"  Calculated: {expr} = {result_str}")
                elif formula:
                    output.append(f"  Formula: {formula}")
                
                # Show fallback information
                fallback_info = None
                for fb_entry in context.fallback_log:
                    if fb_entry.get('variable') == var:
                        source = fb_entry.get('source', 'unknown')
                        if source == 'global_default':
                            fallback_info = "Fallback Used: global_default (original value missing)"
                        elif source == 'previous_period':
                            fallback_info = "Fallback Used: previous_period"
                        elif source == 'zero':
                            fallback_info = "Fallback Used: zero (no data available)"
                        else:
                            fallback_info = f"Fallback Used: {source}"
                        break
                
                if fallback_info:
                    output.append(f"  {fallback_info}")
                else:
                    output.append(f"  No Fallback (calculated from available data)")
                
                # Show validation status
                if var in report_variables:
                    var_config = report_variables[var]['fields']
                    validation_rules = var_config.get('Validation_Rules')
                    expected_values = var_config.get('Expected_Values')
                    
                    # Hard validation status
                    if validation_rules:
                        is_valid, _ = validate_value(result, validation_rules)
                        if is_valid:
                            output.append(f"  ✅ Valid Range: {validation_rules} (PASS)")
                        else:
                            output.append(f"  🚨 Valid Range: {validation_rules} (FAIL)")
                    
                    # Soft validation status  
                    if expected_values and expected_values.lower() not in ['optional', 'not_empty']:
                        is_in_range, _ = check_expected_range(result, expected_values)
                        if is_in_range:
                            output.append(f"  ✅ Expected Range: {expected_values} (PASS)")
                        else:
                            # Determine if it's outside or far outside
                            if isinstance(result, (int, float)):
                                try:
                                    # Parse expected range to determine severity
                                    if '>=' in expected_values and '<=' in expected_values:
                                        parts = expected_values.split('AND')
                                        min_val = float(parts[0].split('>=')[1].strip())
                                        max_val = float(parts[1].split('<=')[1].strip())
                                        range_size = max_val - min_val;
                                        
                                        if result < min_val:
                                            distance = min_val - result
                                            if distance > range_size:
                                                output.append(f"  🚨 Expected Range: {expected_values} (FAR OUTSIDE - Low)")
                                            else:
                                                output.append(f"  ⚠️ Expected Range: {expected_values} (OUTSIDE - Low)")
                                        elif result > max_val:
                                            distance = result - max_val
                                            if distance > range_size:
                                                output.append(f"  🚨 Expected Range: {expected_values} (FAR OUTSIDE - High)")
                                            else:
                                                output.append(f"  ⚠️ Expected Range: {expected_values} (OUTSIDE - High)")
                                    else:
                                        output.append(f"  ⚠️ Expected Range: {expected_values} (OUTSIDE)")
                                except:
                                    output.append(f"  ⚠️ Expected Range: {expected_values} (OUTSIDE)")
                            else:
                                output.append(f"  ⚠️ Expected Range: {expected_values} (OUTSIDE)")
                
                output.append("")
            
            output.append("")
        
        # Add comprehensive summary
        output.append("**DATA QUALITY SUMMARY:**")
        output.append("")
        
        # Count totals
        total_vars = len(context.calculated_values)
        fallback_count = len(context.fallback_log)
        
        # Count fallback types
        fallback_types = {}
        for fb_entry in context.fallback_log:
            source = fb_entry.get('source', 'unknown')
            fallback_types[source] = fallback_types.get(source, 0) + 1
        
        # Count validation results
        validation_pass = 0
        validation_fail = 0
        expected_pass = 0
        expected_outside = 0
        expected_far_outside = 0
        
        for var, value in context.calculated_values.items():
            if var in report_variables:
                var_config = report_variables[var]['fields']
                validation_rules = var_config.get('Validation_Rules')
                expected_values = var_config.get('Expected_Values')
                
                if validation_rules:
                    is_valid, _ = validate_value(value, validation_rules)
                    if is_valid:
                        validation_pass += 1
                    else:
                        validation_fail += 1
                
                if expected_values and expected_values.lower() not in ['optional', 'not_empty']:
                    is_in_range, _ = check_expected_range(value, expected_values)
                    if is_in_range:
                        expected_pass += 1
                    else:
                        # Determine severity for summary
                        if isinstance(value, (int, float)):
                            try:
                                if '>=' in expected_values and '<=' in expected_values:
                                    parts = expected_values.split('AND')
                                    min_val = float(parts[0].split('>=')[1].strip())
                                    max_val = float(parts[1].split('<=')[1].strip())
                                    range_size = max_val - min_val;
                                    
                                    distance = 0
                                    if value < min_val:
                                        distance = min_val - value
                                    elif value > max_val:
                                        distance = value - max_val;
                                    
                                    if distance > range_size:
                                        expected_far_outside += 1
                                    else:
                                        expected_outside += 1
                                else:
                                    expected_outside += 1
                            except:
                                expected_outside += 1
                        else:
                            expected_outside += 1
        
        output.append(f"- **Total Variables:** {total_vars}")
        output.append(f"- **Fallbacks Used:** {fallback_count}")
        
        if fallback_types:
            for source, count in fallback_types.items():
                source_display = source.replace('_', ' ').title()
                output.append(f"  - {source_display}: {count}")
        
        output.append("")
        output.append("- **Validation Results:**")
        
        total_with_validation = validation_pass + validation_fail
        if total_with_validation > 0:
            pass_pct = round((validation_pass / total_with_validation) * 100)
            output.append(f"  - Hard Validation Pass: {validation_pass}/{total_with_validation} ({pass_pct}%)")
            if validation_fail > 0:
                output.append(f"  - Hard Validation Fail: {validation_fail}")
        
        total_with_expected = expected_pass + expected_outside + expected_far_outside
        if total_with_expected > 0:
            pass_pct = round((expected_pass / total_with_expected) * 100)
            output.append(f"  - Within Expected Range: {expected_pass}/{total_with_expected} ({pass_pct}%)")
            if expected_outside > 0:
                output.append(f"  - Outside Expected Range: {expected_outside}")
            if expected_far_outside > 0:
                output.append(f"  - Far Outside Expected Range: {expected_far_outside}")
        
        # Add warnings section
        if context.validation_flags or context.expected_flags:
            output.append("")
            output.append("**WARNINGS:**")
            
            for flag in context.validation_flags:
                output.append(f"🚨 **{flag['variable']}**: {flag['message']}")
            
            for flag in context.expected_flags:
                var = flag['variable']
                value = flag.get('value', 'Unknown')
                
                # Format value for display
                if isinstance(value, float):
                    if value > 100:
                        value_str = f"{value:,.2f}"
                    elif value > 1:
                        value_str = f"{value:.2f}"
                    else:
                        value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                
                # Determine warning level
                if 'FAR OUTSIDE' in flag['message']:
                    output.append(f"🚨 **{var}**: {value_str} (Expected range issue)")
                else:
                    output.append(f"⚠️ **{var}**: {value_str} (Expected range issue)")
        
        return '\n'.join(output)

    # Note: Calculation Log and YTD metadata fields are commented out
    # because they may not exist in the actual Airtable schema
    
    # Add calculation log to the update in formatted text
    report_fields['Calculation Log'] = format_calc_log(context.calculation_log)[:50000]  # Airtable text limit
    
    # Add YTD metadata field
    if 'hhs_ytd' in context.ytd_metadata:
        metadata = context.ytd_metadata['hhs_ytd']
        report_fields['hhs_ytd_metadata'] = json.dumps(metadata, indent=2)[:50000]  # Airtable text limit
    
    try:
        # Filter out fields that are known to be read-only or lookup fields
        readonly_fields = {
            # Removed calculated fields that should be writable:
            # 'lead_to_quote_rate', '%won_website', 'fire_per_hh', 'maass_agent_conversion', 
            # 'commission_rate', 'average_premium_per_household', 'autos_per_hh'
            
            'client_record_id',    # Lookup field
            'client_headshot',     # Lookup field  
            'client_name',         # Lookup field
            'quote_starts',        # Lookup from Keyword Performance
            'sms_clicks',          # Lookup from Keyword Performance
            'phone_clicks',        # Lookup from Keyword Performance
            'total_leads',         # Lookup from My SF Domain
            'conversions',         # Lookup from Keyword Performance
            'cost',                # Lookup from Keyword Performance
            'search_impression_share',  # Lookup field
            'client',              # Lookup field
            'month',               # Lookup field
            'year',                # Lookup field
            'is_full_month',       # Lookup field
            'date_start',          # Lookup field
            'date_end',            # Lookup field
            'record_id',           # Lookup field
            'RID',                 # Lookup field
            'Report_ID',           # Lookup field
        }
        
        # Remove read-only fields from report_fields
        filtered_fields = {k: v for k, v in report_fields.items() if k not in readonly_fields}
        
        print(f"\nDEBUG: Attempting to write {len(filtered_fields)} fields (filtered out {len(report_fields) - len(filtered_fields)} readonly fields)")
        print("DEBUG: Fields being written:")
        for key, value in filtered_fields.items():
            print(f"  {key}: {value}")
        print(f"DEBUG: Source table: {source_table}")
        print(f"DEBUG: Record ID: {context.report_record['id']}")
        print(f"DEBUG: client_report field value: {report_fields.get('client_report')}")
        
        # Additional debugging: Check what table this record actually belongs to
        try:
            # Try to verify the record exists in the expected table
            test_table = base.table(REPORT_DATABASE_TABLE)
            test_record = test_table.get(context.report_record['id'])
            print(f"DEBUG: Record found in {REPORT_DATABASE_TABLE} table")
        except Exception as e:
            print(f"DEBUG: Record NOT found in {REPORT_DATABASE_TABLE} table: {e}")
            try:
                test_table = base.table(GENERATED_REPORTS_TABLE)
                test_record = test_table.get(context.report_record['id'])
                print(f"DEBUG: Record found in {GENERATED_REPORTS_TABLE} table")
            except Exception as e2:
                print(f"DEBUG: Record NOT found in {GENERATED_REPORTS_TABLE} table: {e2}")
        
        # Determine if we should create or update
        if source_table == GENERATED_REPORTS_TABLE:
            # Update existing record in Generated_Reports table
            # Remove client_report field for updates as it's already set
            update_fields = {k: v for k, v in filtered_fields.items() if k != 'client_report'}
            try:
                table.update(context.report_record['id'], update_fields)
                print(f"\n✓ Updated Generated_Report: {context.report_record['id']}")
                return context.report_record['id']
            except Exception as update_error:
                print(f"DEBUG: Update failed, trying create instead: {update_error}")
                # If update fails due to table mismatch, fall back to create logic
                source_table = REPORT_DATABASE_TABLE  # Force create mode
        
        if source_table == REPORT_DATABASE_TABLE:
            # Create new record in Generated_Reports table (source is Client_Reports)
            # First check if a record already exists for this client_report
            try:
                existing_records = table.all(
                    formula=f"{{client_report}} = '{context.report_record['id']}'"
                )
                if existing_records:
                    # Update existing record
                    existing_record_id = existing_records[0]['id']
                    update_fields = {k: v for k, v in filtered_fields.items() if k != 'client_report'}
                    table.update(existing_record_id, update_fields)
                    print(f"\n✓ Updated existing Generated_Report: {existing_record_id}")
                    return existing_record_id
                else:
                    # Create new record
                    new_record = table.create(filtered_fields)
                    print(f"\n✓ Created new Generated_Report: {new_record['id']}")
                    return new_record['id']
            except Exception as search_error:
                print(f"DEBUG: Error searching for existing record: {search_error}")
                # Fallback to creating new record
                new_record = table.create(filtered_fields)
                print(f"\n✓ Created new Generated_Report: {new_record['id']}")
                return new_record['id']
    except Exception as e:
        print(f"\n✗ Error updating Generated_Report: {e}")
        print(f"DEBUG: BASE_ID = {BASE_ID}")
        print(f"DEBUG: Table name = {table.name if hasattr(table, 'name') else table}")
        print(f"DEBUG: Fields attempted: {list(report_fields.keys())}")
        return None


def validate_value(value, validation_rules):
    """
    Validate a value against validation rules (hard validation - red flags)
    
    Args:
        value: The value to validate
        validation_rules: String expression like ">= 0 AND <= 1" or "not_empty"
    
    Returns:
        (is_valid: bool, message: str)
    """
    if not validation_rules or value is None:
        return True, ""
    
    try:
        # Handle special cases
        if validation_rules == "not_empty":
            is_valid = value is not None and str(value).strip() != ""
            if not is_valid:
                return False, f"Validation failed: '{value}' is empty but should not be"
            return True, ""
        
        if "integer" in validation_rules.lower():
            # Check if it's an integer
            try:
                int_value = int(float(value))
                if int_value != float(value):
                    return False, f"Validation failed: {value} is not an integer"
                value = int_value  # Use integer value for range checks
            except (ValueError, TypeError):
                return False, f"Validation failed: {value} is not a valid integer"
            # Remove "integer" from the rules for further processing
            validation_rules = validation_rules.replace("AND integer", "").replace("integer AND", "").replace("integer", "").strip()
            if not validation_rules:
                return True, ""  # Only integer check was needed
        
        # Parse comparison expressions
        # Replace logical operators
        expression = validation_rules.replace('AND', 'and').replace('OR', 'or')
        
        # Ensure value is numeric for comparisons
        try:
            numeric_value = parse_numeric_value(value)
        except ValueError as e:
            return False, f"Validation error: {e}"
        
        # Split by 'and' and 'or' to handle each condition
        import re
        
        # Parse individual conditions
        conditions = re.split(r'\s+(and|or)\s+', expression)
        operators = re.findall(r'\s+(and|or)\s+', expression)
        
        results = []
        for i, condition in enumerate(conditions):
            if condition.strip() in ['and', 'or']:
                continue
                
            condition = condition.strip()
            
            # Handle different comparison operators
            if '>=' in condition:
                threshold = float(condition.split('>=')[1].strip())
                results.append(numeric_value >= threshold)
            elif '<=' in condition:
                threshold = float(condition.split('<=')[1].strip())
                results.append(numeric_value <= threshold)
            elif '>' in condition:
                threshold = float(condition.split('>')[1].strip())
                results.append(numeric_value > threshold)
            elif '<' in condition:
                threshold = float(condition.split('<')[1].strip())
                results.append(numeric_value < threshold)
            elif '=' in condition:
                threshold = float(condition.split('=')[1].strip())
                results.append(abs(numeric_value - threshold) < 1e-10)  # Float equality check
            else:
                return False, f"Validation error: Could not parse condition '{condition}'"
        
        # Combine results with logical operators
        if not results:
            return True, ""
        
        final_result = results[0]
        for i, op in enumerate(operators):
            if i + 1 < len(results):
                if 'and' in op:
                    final_result = final_result and results[i + 1]
                elif 'or' in op:
                    final_result = final_result or results[i + 1]
        
        if final_result:
            return True, ""
        else:
            return False, f"Validation failed: {numeric_value} does not satisfy '{validation_rules}'"
            
    except Exception as e:
        return False, f"Validation error: {e}"


def check_expected_range(value, expected_values):
    """
    Check if a value falls within expected ranges (soft validation - yellow flags)
    
    Args:
        value: The value to check
        expected_values: String expression like ">= 0.09 AND <= 0.25", "= 0.90", or "optional"
    
    Returns:
        (is_in_range: bool, message: str)
    """
    if not expected_values or value is None:
        return True, ""
    
    try:
        # Handle special cases
        if expected_values.lower() in ["optional", "not_empty"]:
            return True, ""  # No range check needed for optional fields
        
        # Parse comparison expressions (reuse logic from validate_value)
        expression = expected_values.replace('AND', 'and').replace('OR', 'or')
        
        # Ensure value is numeric for comparisons
        try:
            numeric_value = parse_numeric_value(value)
        except ValueError as e:
            return False, f"Expected range check error: {e}"
        
        # Split by 'and' and 'or' to handle each condition
        import re
        
        # Parse individual conditions
        conditions = re.split(r'\s+(and|or)\s+', expression)
        operators = re.findall(r'\s+(and|or)\s+', expression)
        
        results = []
        for i, condition in enumerate(conditions):
            if condition.strip() in ['and', 'or']:
                continue
                
            condition = condition.strip()
            
            # Handle different comparison operators
            if '>=' in condition:
                threshold = float(condition.split('>=')[1].strip())
                results.append(numeric_value >= threshold)
            elif '<=' in condition:
                threshold = float(condition.split('<=')[1].strip())
                results.append(numeric_value <= threshold)
            elif '>' in condition:
                threshold = float(condition.split('>')[1].strip())
                results.append(numeric_value > threshold)
            elif '<' in condition:
                threshold = float(condition.split('<')[1].strip())
                results.append(numeric_value < threshold)
            elif '=' in condition:
                threshold = float(condition.split('=')[1].strip())
                results.append(abs(numeric_value - threshold) < 1e-10)  # Float equality check
            else:
                return False, f"Expected range check error: Could not parse condition '{condition}'"
        
        # Combine results with logical operators
        if not results:
            return True, ""
        
        final_result = results[0]
        for i, op in enumerate(operators):
            if i + 1 < len(results):
                if 'and' in op:
                    final_result = final_result and results[i + 1]
                elif 'or' in op:
                    final_result = final_result or results[i + 1]
        
        if final_result:
            return True, ""
        else:
            return False, f"Outside expected range: {numeric_value} does not meet '{expected_values}'"
            
    except Exception as e:
        return False, f"Expected range check error: {e}"


def validate_all_calculated_values(context: CalculationContext, report_variables: Dict[str, dict]):
    """
    Validate all calculated values against their validation rules and expected ranges
    
    Args:
        context: The calculation context with calculated values
        report_variables: Dictionary of variable configurations
    """
    validation_flags = []
    expected_flags = []
    
    for var_name, value in context.calculated_values.items():
        if var_name in report_variables:
            var_config = report_variables[var_name]['fields']
            
            # Hard validation (red flags)
            validation_rules = var_config.get('Validation_Rules')
            if validation_rules:
                is_valid, validation_msg = validate_value(value, validation_rules)
                if not is_valid:
                    validation_flags.append({
                        'variable': var_name,
                        'value': value,
                        'message': validation_msg,
                        'type': 'validation_error'
                    })
                    context.errors.append(f"🔴 {var_name}: {validation_msg}")
            
            # Soft validation (yellow flags)
            expected_values = var_config.get('Expected_Values')  
            if expected_values:
                is_in_range, expected_msg = check_expected_range(value, expected_values)
                if not is_in_range:
                    expected_flags.append({
                        'variable': var_name,
                        'value': value,
                        'message': expected_msg,
                        'type': 'expected_range_warning'
                    })
                    context.warnings.append(f"🟡 {var_name}: {expected_msg}")
    
    # Store validation results in context for reporting
    context.validation_flags = validation_flags
    context.expected_flags = expected_flags
    
    print(f"\n📊 Validation Summary:")
    print(f"  🔴 Hard validation errors: {len(validation_flags)}")
    print(f"  🟡 Expected range warnings: {len(expected_flags)}")
    
    if validation_flags:
        print(f"\n🔴 Validation Errors:")
        for flag in validation_flags:
            print(f"  {flag['variable']}: {flag['message']}")
    
    if expected_flags:
        print(f"\n🟡 Expected Range Warnings:")
        for flag in expected_flags:
            print(f"  {flag['variable']}: {flag['message']}")


def main(report_database_id: Optional[str] = None):
    """
    Main function to run calculation engine
    
    Args:
        report_database_id: ID of Report_Database record to process
    """
    
    print("="*70)
    print("REPORT CALCULATION ENGINE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Load configuration
    print("\nLoading configuration...")
    
    # Load dependency analysis
    try:
        with open('dependency_analysis.json', 'r') as f:
            dependency_analysis = json.load(f)
        print("✓ Loaded dependency analysis")
    except FileNotFoundError:
        print("✗ dependency_analysis.json not found. Run dependency_analyzer.py first.")
        return
    
    # Load report variables
    report_variables = load_report_variables()
    print(f"✓ Loaded {len(report_variables)} report variables")
    
    # Load global variables
    global_vars = load_global_variables()
    print(f"✓ Loaded {len(global_vars)} global default values")
    
    # Get report to process
    source_table = REPORT_DATABASE_TABLE  # Default to Client_Reports
    if not report_database_id:
        # Get most recent unprocessed report
        table = base.table(REPORT_DATABASE_TABLE)
        records = table.all(
            formula="NOT({Processed})",
            sort=['-date_start', '-date_end'],
            max_records=1
        )
        
        if not records:
            print("\n✗ No unprocessed reports found")
            return
        
        report_record = records[0]
        report_database_id = report_record['id']
        source_table = REPORT_DATABASE_TABLE
    else:
        # Load specific report - try both tables to auto-detect
        print(f"DEBUG: BASE_ID = {BASE_ID}")
        print(f"DEBUG: Trying to load record: {report_database_id}")
        
        # First try Generated_Reports table (for rerunning existing calculations)
        try:
            table = base.table(GENERATED_REPORTS_TABLE)
            report_record = table.get(report_database_id)
            source_table = GENERATED_REPORTS_TABLE
            print(f"DEBUG: Found record in {GENERATED_REPORTS_TABLE} table")
        except Exception:
            # If not found, try Client_Reports table (for new calculations)
            try:
                table = base.table(REPORT_DATABASE_TABLE)
                report_record = table.get(report_database_id)
                source_table = REPORT_DATABASE_TABLE
                print(f"DEBUG: Found record in {REPORT_DATABASE_TABLE} table")
            except Exception as e:
                print(f"✗ Record {report_database_id} not found in either table: {e}")
                return
    
    print(f"\nProcessing report: {report_database_id}")
    
    # Get client ID from the client field (which contains lookup to client record)
    client_field = report_record['fields'].get('client')
    if client_field and isinstance(client_field, list):
        client_id = client_field[0] if client_field else None
    else:
        client_id = client_field
        
    if not client_id:
        print("✗ No client linked to report (client field missing or empty)")
        return
    
    # Create calculation context
    context = CalculationContext(client_id, report_record)
    
    # Run calculations
    success = calculate_all_variables(
        context,
        dependency_analysis,
        report_variables,
        global_vars
    )
    
    # Write results
    if success or len(context.calculated_values) > 10:  # Even partial results might be valuable
        generated_report_id = write_to_generated_reports(context, report_variables, source_table)
        
        if generated_report_id:
            # Optionally mark Report_Database record as processed (only if field exists)
            # Remove or comment out the following block if 'Processed' is not needed:
            # table = base.table(REPORT_DATABASE_TABLE)
            # table.update(report_database_id, {
            #     'Processed': True,
            #     'Generated Report': [generated_report_id]
            # })
            pass
    
    # Save detailed log
    log_data = {
        'report_database_id': report_database_id,
        'timestamp': datetime.now().isoformat(),
        'calculated_values': len(context.calculated_values),
        'fallbacks_used': len(context.fallback_log),
        'errors': context.errors,
        'warnings': context.warnings,
        'calculation_log': context.calculation_log,
        'fallback_log': context.fallback_log
    }
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    with open(f'logs/calculation_log_{report_database_id}.json', 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\n✓ Detailed log saved to logs/calculation_log_{report_database_id}.json")
    print("="*70)


if __name__ == "__main__":
    import sys
    
    # Allow passing report ID as command line argument
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()