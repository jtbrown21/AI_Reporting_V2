#!/usr/bin/env python3
"""
Report Generator for Automated HTML Report Generation

This script:
1. Takes calculated values from the calculation engine
2. Maps them to the HTML template variables
3. Generates a static HTML report
4. Commits and pushes to GitHub Pages
5. Provides webhook endpoint for n8n integration
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import re
from pyairtable import Api
from dotenv import load_dotenv
import github

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')  # e.g., "username/repo-name"
GITHUB_PAGES_BRANCH = os.environ.get('GITHUB_PAGES_BRANCH', 'gh-pages')

# Table names
GENERATED_REPORTS_TABLE = 'Generated_Reports'

class ReportGenerator:
    """Main class for generating and deploying HTML reports"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        
        if not AIRTABLE_API_KEY:
            raise ValueError("AIRTABLE_API_KEY environment variable is not set")
        if not BASE_ID:
            raise ValueError("AIRTABLE_BASE_ID environment variable is not set")
        self.api = Api(AIRTABLE_API_KEY)
        self.base = self.api.base(BASE_ID)
        self.template_path = Path(__file__).parent.parent / "templates" / "v2.html"
        self.output_dir = Path(__file__).parent.parent / "reports"
        self.github_pages_dir = Path(__file__).parent.parent / "gh-pages"
        
        # Initialize GitHub client for API-based deployment
        self.github_token = GITHUB_TOKEN
        self.github_repo = GITHUB_REPO
        if self.github_token:
            self.github_client = github.Github(self.github_token)
        else:
            self.github_client = None
        
        # Set development directory for test mode
        self.development_dir = Path(__file__).parent.parent / "templates" / "development"
    
    def get_report_data(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Fetch report data from Airtable Generated_Reports table"""
        try:
            table = self.base.table(GENERATED_REPORTS_TABLE)
            record = table.get(report_id)
            return record['fields']
        except Exception as e:
            print(f"Error fetching report {report_id}: {e}")
            return None
    
    def _get_variable_data_types(self) -> Dict[str, str]:
        """Fetch and cache variable data types from the Report_Variables table."""
        if hasattr(self, '_variable_data_types'):
            return self._variable_data_types
        data_types = {}
        try:
            table = self.base.table('Report_Variables')
            records = table.all()
            
            for record in records:
                # Use Variable_ID instead of Variable_Name
                name = record['fields'].get('Variable_ID')
                dtype = record['fields'].get('Data_Type')
                if name and dtype:
                    data_types[name] = dtype.lower()
        except Exception as e:
            print(f"Warning: Could not fetch variable data types: {e}")
        self._variable_data_types = data_types
        return data_types

    def _get_variable_display_decimals(self) -> Dict[str, int]:
        """Fetch and cache variable display decimals from the Report_Variables table."""
        if hasattr(self, '_variable_display_decimals'):
            return self._variable_display_decimals
        display_decimals = {}
        try:
            table = self.base.table('Report_Variables')
            records = table.all()
            
            for record in records:
                # Use Variable_ID instead of Variable_Name
                name = record['fields'].get('Variable_ID')
                decimals = record['fields'].get('Display_Decimals')
                if name and decimals is not None:
                    try:
                        display_decimals[name] = int(decimals)
                    except Exception as e:
                        print(f"Warning: Could not convert decimals for {name}: {e}")
        except Exception as e:
            print(f"Warning: Could not fetch variable display decimals: {e}")
        self._variable_display_decimals = display_decimals
        return display_decimals

    def format_value(self, value: Any, field_name: str) -> str:
        """Format values for display in HTML, using ONLY Report_Variables data type and Display_Decimals."""
        if value is None:
            return "0"

        # Check data type and display decimals from Report_Variables
        data_types = self._get_variable_data_types()
        display_decimals = self._get_variable_display_decimals()
        dtype = data_types.get(field_name)
        decimals = display_decimals.get(field_name)

        # Extract actual value from lists if needed
        if isinstance(value, list) and value:
            value = value[0]

        # Convert to numeric if possible
        numeric_value = None
        if isinstance(value, (int, float)):
            numeric_value = value
        elif isinstance(value, str):
            try:
                # Handle percentage strings
                if value.endswith('%'):
                    numeric_value = float(value.strip('%')) / 100.0
                else:
                    numeric_value = float(value)
            except ValueError:
                pass

        # Apply formatting based on Data_Type from Airtable
        if dtype == 'percentage':
            if numeric_value is not None:
                # Default to 0 decimals for percentages if not specified
                decimal_places = decimals if decimals is not None else 0
                percentage_value = numeric_value * 100
                return f"{percentage_value:.{decimal_places}f}%"
            return str(value)
        
        elif dtype == 'currency':
            if numeric_value is not None:
                # Default to 0 decimals for currency if not specified
                decimal_places = decimals if decimals is not None else 0
                formatted_number = f"{numeric_value:,.{decimal_places}f}"
                return f"${formatted_number}"
            return str(value)
        
        elif dtype == 'number':
            if numeric_value is not None:
                # Use specified decimals, or default to 0 for whole numbers, 2 for decimals
                if decimals is not None:
                    return f"{numeric_value:.{decimals}f}"
                else:
                    # Default: integers get 0 decimals, floats get 1 decimal if they have fractional part
                    if numeric_value == int(numeric_value):
                        return f"{int(numeric_value)}"
                    else:
                        return f"{numeric_value:.1f}"
            return str(value)
        
        elif dtype == 'decimal':
            if numeric_value is not None:
                decimal_places = decimals if decimals is not None else 2
                return f"{numeric_value:.{decimal_places}f}"
            return str(value)
        
        elif dtype == 'integer':
            if numeric_value is not None:
                if decimals is not None and decimals > 0:
                    return f"{numeric_value:.{decimals}f}"
                else:
                    return f"{int(round(numeric_value))}"
            return str(value)
        
        elif dtype == 'text':
            # For text fields, just return as string
            return str(value)
        
        elif dtype == 'image':
            # Special handling for client_headshot field
            if field_name == 'client_headshot':
                return self._extract_image_url(value)
            # For other image fields, return as is (the template will handle image processing)
            return str(value)
        
        # If no Data_Type specified in Airtable, return as string
        return str(value)
    
    def create_template_mapping(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Create mapping from template fields to formatted values using direct Airtable field names"""
        mapping = {}
        
        # Direct mapping: use Airtable field names directly in template
        for field_name, value in report_data.items():
            if value is not None:
                # Special handling for client_name: extract from list if needed
                if field_name == 'client_name' and isinstance(value, list):
                    formatted_value = self.format_value(value[0] if value else '', field_name)
                else:
                    formatted_value = self.format_value(value, field_name)
                mapping[field_name] = formatted_value
        
        # Special handling for date formatting
        if 'date_end' in report_data:
            date_end = report_data['date_end']
            # Handle if date_end is a list
            if isinstance(date_end, list) and date_end:
                date_end_value = date_end[0]
            else:
                date_end_value = date_end
            if isinstance(date_end_value, str):
                try:
                    dt = datetime.fromisoformat(date_end_value)
                    mapping['month'] = dt.strftime("%B %Y").upper()
                except Exception:
                    pass  # Do not set 'month' if parsing fails
        
        # Handle monthly HHS data from YTD metadata
        self._process_monthly_hhs_data(report_data, mapping)
        
        # Handle lead-share fields - these might be calculated or placeholder
        if 'lead-share' not in mapping:
            mapping['lead-share'] = ''
        if 'lead-share-bar' not in mapping:
            mapping['lead-share-bar'] = ''
        
        return mapping
    
    def _process_monthly_hhs_data(self, report_data: Dict[str, Any], mapping: Dict[str, str]):
        """Process monthly HHS data from YTD metadata"""
        import json
        
        # Month number to name mapping
        month_names = {
            '1': 'jan', '2': 'feb', '3': 'mar', '4': 'apr', '5': 'may', '6': 'jun',
            '7': 'jul', '8': 'aug', '9': 'sep', '10': 'oct', '11': 'nov', '12': 'dec'
        }
        
        # Initialize all months as empty by default (for bar chart)
        for month_num, month_name in month_names.items():
            mapping[f'hhs_{month_name}'] = ''
        
        # Process YTD metadata if available
        if 'hhs_ytd_metadata' in report_data:
            try:
                ytd_metadata = report_data['hhs_ytd_metadata']
                
                # Handle string JSON or dict
                if isinstance(ytd_metadata, str):
                    ytd_metadata = json.loads(ytd_metadata)
                
                # Extract months data
                if isinstance(ytd_metadata, dict) and 'months' in ytd_metadata:
                    months_data = ytd_metadata['months']
                    
                    for month_num, value in months_data.items():
                        if month_num in month_names:
                            month_name = month_names[month_num]
                            # If value is "missing", leave as empty string
                            if value != "missing":
                                # Use the same formatting logic as {hhs}
                                mapping[f'hhs_{month_name}'] = self.format_value(value, 'hhs')
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Could not parse YTD metadata: {e}")
        
        # Handle current month - should show current month's HHS value
        if 'date_end' in report_data:
            try:
                date_end = report_data['date_end']
                if isinstance(date_end, str):
                    dt = datetime.fromisoformat(date_end)
                    current_month_num = str(dt.month)
                    
                    if current_month_num in month_names:
                        current_month_name = month_names[current_month_num]
                        
                        # Use current month's HHS value
                        if 'hhs' in report_data and report_data['hhs'] is not None:
                            current_hhs = self.format_value(report_data['hhs'], 'hhs')
                            mapping[f'hhs_{current_month_name}'] = current_hhs
                            
            except (ValueError, AttributeError) as e:
                print(f"Warning: Could not determine current month: {e}")
        
        # If no date_end, fall back to current system date
        if all(mapping[f'hhs_{month_names[str(i)]}'] == '' for i in range(1, 13)):
            # If all months are still empty, try to set current month based on today's date
            current_month_num = str(datetime.now().month)
            if current_month_num in month_names:
                current_month_name = month_names[current_month_num]
                if 'hhs' in report_data and report_data['hhs'] is not None:
                    current_hhs = self.format_value(report_data['hhs'], 'hhs')
                    mapping[f'hhs_{current_month_name}'] = current_hhs
    
    def generate_html_report(self, report_data: Dict[str, Any], client_name: str) -> tuple[str, str]:
        """Generate HTML report from template and data"""
        # Read template
        with open(self.template_path, 'r') as f:
            html_content = f.read()
        
        # Create value mapping
        value_mapping = self.create_template_mapping(report_data)
        
        # Replace values in HTML using data-field attributes
        for field, value in value_mapping.items():
            # Skip chart month labels - they should keep their month names, not show values
            if field.startswith('hhs_') and field.endswith(('_jan', '_feb', '_mar', '_apr', '_may', '_jun', 
                                                           '_jul', '_aug', '_sep', '_oct', '_nov', '_dec')):
                continue
            if field in ['hhs_jan', 'hhs_feb', 'hhs_mar', 'hhs_apr', 'hhs_may', 'hhs_jun',
                        'hhs_jul', 'hhs_aug', 'hhs_sep', 'hhs_oct', 'hhs_nov', 'hhs_dec']:
                continue
                
            # Special handling for client_headshot - set as background-image style
            if field == 'client_headshot' and value:
                # Look for the profile-img div and add background-image style
                pattern = r'(<div[^>]*class="[^"]*profile-img[^"]*"[^>]*data-field="client_headshot"[^>]*)(>)'
                def replace_func(match):
                    existing_attrs = match.group(1)
                    # Check if style attribute already exists
                    if 'style=' in existing_attrs:
                        # Add to existing style
                        style_pattern = r'(style="[^"]*)'
                        style_replacement = f'\\1; background-image: url({value}); background-size: cover; background-position: center; border-radius: 50%; overflow: hidden'
                        updated_attrs = re.sub(style_pattern, style_replacement, existing_attrs)
                    else:
                        # Add new style attribute
                        updated_attrs = f'{existing_attrs} style="background-image: url({value}); background-size: cover; background-position: center; border-radius: 50%; overflow: hidden"'
                    return f'{updated_attrs}{match.group(2)}'
                html_content = re.sub(pattern, replace_func, html_content)
            else:
                # Handle normal field replacements for both span and div tags
                for tag in ['span', 'div']:
                    pattern = f'(<{tag}[^>]*data-field="{field}"[^>]*>)[^<]*(</{tag}>)'
                    # Use a function replacement to avoid regex group reference issues
                    def replace_func(match):
                        return f'{match.group(1)}{value}{match.group(2)}'
                    html_content = re.sub(pattern, replace_func, html_content)
        
        # Process chart bars to set dynamic heights and values
        html_content = self._process_chart_data(html_content, value_mapping)
        
        # Generate filename
        report_date = datetime.now().strftime("%Y-%m-%d")
        safe_client_name = re.sub(r'[^a-zA-Z0-9-]', '', client_name.replace(' ', '-'))
        filename = f"{safe_client_name}-{report_date}.html"
        
        return html_content, filename
    
    def save_report(self, html_content: str, filename: str) -> str:
        """Save report to local directory"""
        # Choose output directory based on test mode
        if self.test_mode:
            output_dir = self.development_dir
        else:
            output_dir = self.output_dir
        
        # Ensure output directory exists
        output_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = output_dir / filename
        with open(file_path, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Report saved to {file_path}")
        return str(file_path)
    
    def setup_github_pages(self):
        """Setup GitHub Pages repository - No setup needed for GitHub API approach"""
        if not self.github_client or not self.github_repo:
            print("✗ GitHub client or repo not configured")
            return False
        
        print("✓ GitHub API client configured")
        return True
    
    def publish_report_to_github(self, report_content: str, file_path: str, commit_message: str) -> bool:
        """
        Publish the generated report directly to GitHub repository via API
        """
        if not self.github_client or not self.github_repo:
            print("✗ GitHub client or repo not configured")
            return False
            
        try:
            # Get the repository
            repo = self.github_client.get_repo(self.github_repo)
            
            # Check if file already exists
            try:
                existing_file = repo.get_contents(file_path)
                # Handle the case where get_contents returns a list
                if isinstance(existing_file, list):
                    existing_file = existing_file[0]
                # Update existing file
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=report_content,
                    sha=existing_file.sha
                )
                print(f"✓ Updated existing report at {file_path}")
            except github.GithubException:
                # Create new file if it doesn't exist
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=report_content
                )
                print(f"✓ Created new report at {file_path}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error publishing report: {str(e)}")
            return False

    def deploy_to_github_via_api(self, html_content: str, filename: str) -> Optional[str]:
        """Deploy report to GitHub via API (replaces git operations)"""
        if not self.github_client or not self.github_repo:
            print("✗ GitHub client or repo not configured")
            return None
            
        try:
            # Create GitHub path for the report
            github_path = f"reports/{filename}"
            
            # Create commit message
            commit_message = f"Update report: {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Publish via GitHub API
            if self.publish_report_to_github(html_content, github_path, commit_message):
                # Also update index.html with latest report
                index_commit_message = f"Update index.html with latest report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.publish_report_to_github(html_content, "index.html", index_commit_message)
                
                # Generate URL
                repo_name = self.github_repo.split('/')[-1]
                github_url = f"https://{self.github_repo.split('/')[0]}.github.io/{repo_name}/reports/{filename}"
                
                print(f"✓ Report available at GitHub Pages: {github_url}")
                return github_url
            else:
                print(f"✗ Failed to deploy {filename}")
                return None
                
        except Exception as e:
            print(f"✗ Error during GitHub API deployment: {str(e)}")
            return None

    def deploy_to_github_pages(self, html_content: str, filename: str) -> Optional[str]:
        """Deploy report to GitHub Pages via API (replaces git operations)"""
        return self.deploy_to_github_via_api(html_content, filename)
    
    def validate_data_mapping(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data mapping and return validation results"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'field_mappings': {},
            'missing_fields': [],
            'extra_fields': [],
            'formatted_values': {}
        }
        
        # Check for required fields
        required_fields = ['client_name', 'hhs', 'est_auto', 'est_fire', 'est_annual_commission']
        for field in required_fields:
            if field not in report_data:
                validation_results['missing_fields'].append(field)
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False
        
        # Check for fields not in report data (we'll accept any field since we're using direct mapping)
        # This validation is less strict now since we use direct Airtable field names
        extra_fields = []  # No longer checking against a mapping file
        
        # Create value mapping and validate formatting
        value_mapping = self.create_template_mapping(report_data)
        validation_results['field_mappings'] = value_mapping
        
        # Validate numeric fields
        numeric_fields = ['hhs', 'est_auto', 'est_fire', 'est_annual_commission', 'year1_return']
        for field in numeric_fields:
            if field in report_data:
                try:
                    float(report_data[field])
                    validation_results['formatted_values'][field] = self.format_value(report_data[field], field)
                except (ValueError, TypeError):
                    validation_results['errors'].append(f"Invalid numeric value for {field}: {report_data[field]}")
                    validation_results['valid'] = False
        
        # Validate client name
        if 'client_name' in report_data:
            client_name = report_data['client_name']
            if isinstance(client_name, list):
                client_name = client_name[0] if client_name else ''
            if not client_name or client_name.strip() == '':
                validation_results['errors'].append("Client name is empty")
                validation_results['valid'] = False
        
        return validation_results
    
    def generate_test_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Generate a test report with validation information"""
        print(f"🧪 Running test mode for report ID: {report_id}")
        
        # Get report data
        report_data = self.get_report_data(report_id)
        if not report_data:
            print(f"✗ Could not fetch report data for {report_id}")
            return None
        
        # Validate data mapping
        validation_results = self.validate_data_mapping(report_data)
        
        # Print validation results
        print("\n📊 Data Validation Results:")
        print(f"Valid: {'✓' if validation_results['valid'] else '✗'}")
        
        if validation_results['errors']:
            print("\n❌ Errors:")
            for error in validation_results['errors']:
                print(f"  - {error}")
        
        if validation_results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in validation_results['warnings']:
                print(f"  - {warning}")
        
        if validation_results['missing_fields']:
            print(f"\n🔍 Missing fields: {', '.join(validation_results['missing_fields'])}")
        
        if validation_results['extra_fields']:
            print(f"\n➕ Extra fields: {', '.join(validation_results['extra_fields'])}")
        
        print(f"\n📋 Field Mappings ({len(validation_results['field_mappings'])} fields):")
        for template_field, formatted_value in validation_results['field_mappings'].items():
            print(f"  {template_field}: {formatted_value}")
        
        # Generate HTML even if validation fails (for debugging)
        client_name = report_data.get('client_name', 'Test Client')
        if isinstance(client_name, list):
            client_name = client_name[0] if client_name else 'Test Client'
        
        print(f"\n🏗️  Generating HTML report for client: {client_name}")
        html_content, filename = self.generate_html_report(report_data, client_name)
        
        # Save to development directory
        file_path = self.save_report(html_content, filename)
        
        # Create validation report
        validation_filename = f"validation_{filename.replace('.html', '.json')}"
        validation_file_path = self.development_dir / validation_filename
        
        with open(validation_file_path, 'w') as f:
            json.dump({
                'report_id': report_id,
                'client_name': client_name,
                'validation_results': validation_results,
                'report_data': report_data,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"✓ Validation report saved to {validation_file_path}")
        
        return {
            'html_file': file_path,
            'validation_file': str(validation_file_path),
            'validation_results': validation_results,
            'client_name': client_name
        }
    
    def generate_and_deploy(self, report_id: str) -> Optional[str]:
        """Main function to generate and deploy a report"""
        if self.test_mode:
            # Run in test mode - no deployment
            test_results = self.generate_test_report(report_id)
            return test_results['html_file'] if test_results else None
        
        print(f"Generating report for ID: {report_id}")
        
        # Get report data
        report_data = self.get_report_data(report_id)
        if not report_data:
            print(f"✗ Could not fetch report data for {report_id}")
            return None
        
        # Get client name
        client_name = report_data.get('client_name', 'Unknown Client')
        if isinstance(client_name, list):
            client_name = client_name[0] if client_name else 'Unknown Client'
        
        print(f"Generating report for client: {client_name}")
        
        # Generate HTML
        html_content, filename = self.generate_html_report(report_data, client_name)
        
        # Save locally
        local_path = self.save_report(html_content, filename)
        
        # Deploy to GitHub Pages
        github_url = self.deploy_to_github_pages(html_content, filename)
        
        if github_url:
            # Update Airtable record with GitHub URL
            try:
                table = self.base.table(GENERATED_REPORTS_TABLE)
                table.update(report_id, {
                    'Report URL': github_url
                })
                print(f"✓ Updated Airtable record with Report URL: {github_url}")
            except Exception as e:
                print(f"✗ Error updating Airtable record: {e}")
        
        return github_url
    
    def debug_report_variables_table(self):
        """Debug function to inspect the Report_Variables table structure"""
        print("\n" + "="*60)
        print("REPORT_VARIABLES TABLE DEBUG")
        print("="*60)
        
        try:
            table = self.base.table('Report_Variables')
            records = table.all()
            print(f"Found {len(records)} records in Report_Variables table")
            
            if not records:
                print("❌ No records found in Report_Variables table!")
                return
            
            # Show structure of first record
            first_record = records[0]
            print(f"\nFirst record structure:")
            print(f"Record ID: {first_record.get('id')}")
            print(f"Available fields: {list(first_record['fields'].keys())}")
            
            # Show all records
            print(f"\nAll records:")
            for i, record in enumerate(records):
                fields = record['fields']
                print(f"\nRecord {i+1} (ID: {record.get('id')}):")
                for field_name, field_value in fields.items():
                    print(f"  {field_name}: {field_value} (type: {type(field_value)})")
            
            # Check for common field name variations
            common_variations = [
                'Variable_Name', 'Variable Name', 'variable_name', 'name', 'Name',
                'Data_Type', 'Data Type', 'data_type', 'type', 'Type',
                'Display_Decimals', 'Display Decimals', 'display_decimals', 'decimals', 'Decimals'
            ]
            
            print(f"\nChecking for common field name variations:")
            first_fields = first_record['fields'].keys()
            for variation in common_variations:
                if variation in first_fields:
                    print(f"  ✓ Found: {variation}")
                else:
                    print(f"  ✗ Missing: {variation}")
                    
        except Exception as e:
            print(f"❌ Error accessing Report_Variables table: {e}")
        
        print("="*60)
    
    def _extract_image_url(self, attachment_data: Any) -> str:
        """Extract the full-size image URL from Airtable attachment data."""
        try:
            # Handle case where attachment_data is a dictionary (single attachment)
            if isinstance(attachment_data, dict):
                url = attachment_data.get('url')
                if url:
                    return url
            
            # Handle case where attachment_data is a list (multiple attachments)
            elif isinstance(attachment_data, list) and attachment_data:
                first_attachment = attachment_data[0]
                if isinstance(first_attachment, dict):
                    url = first_attachment.get('url')
                    if url:
                        return url
            
            # Handle case where attachment_data is a string (JSON)
            elif isinstance(attachment_data, str):
                import json
                try:
                    parsed = json.loads(attachment_data)
                    return self._extract_image_url(parsed)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Warning: Could not extract image URL from {attachment_data}: {e}")
        
        # Return empty string if extraction fails
        return ""

    def _process_chart_bars(self, html_content: str, report_data: Dict[str, Any]) -> str:
        """Process chart bars to set dynamic heights and ensure all bars have values."""
        # Monthly HHS fields in order
        months = ['hhs_jan', 'hhs_feb', 'hhs_mar', 'hhs_apr', 'hhs_may', 'hhs_jun', 
                 'hhs_jul', 'hhs_aug', 'hhs_sep', 'hhs_oct', 'hhs_nov', 'hhs_dec']
        
        # Get monthly values
        monthly_values = []
        for month in months:
            value = report_data.get(month, 0)
            if value is None or value == '':
                value = 0
            try:
                monthly_values.append(float(value))
            except (ValueError, TypeError):
                monthly_values.append(0.0)
        
        print(f"[DEBUG] Monthly values: {dict(zip(months, monthly_values))}")
        
        # Calculate dynamic heights (max height = 160px, min = 20px for non-zero values)
        max_value = max(monthly_values) if any(v > 0 for v in monthly_values) else 1
        max_height = 160
        min_height = 20
        
        print(f"[DEBUG] Max value: {max_value}")
        
        # Use a simpler approach - replace each chart bar one by one
        import re
        
        # Find all chart-bar-wrapper sections
        pattern = r'<div class="chart-bar-wrapper">\s*<div class="chart-bar"[^>]*style="[^"]*"[^>]*>.*?</div>\s*</div>'
        matches = list(re.finditer(pattern, html_content, re.DOTALL))
        
        print(f"[DEBUG] Found {len(matches)} chart bars")
        
        # Replace from the end to avoid index shifting
        for i in reversed(range(len(matches))):
            if i < len(months):
                month_field = months[i]
                value = monthly_values[i]
                
                # Calculate height
                if value > 0:
                    height = int((value / max_value) * max_height)
                    if height < min_height:
                        height = min_height
                else:
                    height = 0
                
                print(f"[DEBUG] {month_field}: value={value}, height={height}px")
                
                # Format value for display
                formatted_value = self.format_value(value, month_field) if value > 0 else ""
                
                # Create the replacement content
                if value > 0:
                    replacement = f'<div class="chart-bar-wrapper"><div class="chart-bar" style="height: {height}px;"><span class="chart-bar-value swap-target" data-field="{month_field}">{formatted_value}</span></div></div>'
                else:
                    replacement = f'<div class="chart-bar-wrapper"><div class="chart-bar" style="height: {height}px;"></div></div>'
                
                # Replace in HTML
                match = matches[i]
                html_content = html_content[:match.start()] + replacement + html_content[match.end():]
        
        return html_content

    def _process_chart_data(self, html_content: str, value_mapping: Dict[str, str]) -> str:
        """Process chart data to set dynamic bar heights and values based on monthly HHS data."""
        
        # Get monthly data from value_mapping (which includes processed hhs_jan, hhs_feb, etc.)
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        monthly_values = []
        
        for month in months:
            field_name = f'hhs_{month}'
            value_str = value_mapping.get(field_name, '0')
            
            # Convert to numeric value
            try:
                if value_str and value_str.strip():
                    value = float(value_str)
                else:
                    value = 0.0
            except:
                value = 0.0
            
            monthly_values.append(value)
        
        # Calculate max value for scaling (avoid division by zero)
        max_value = max(monthly_values) if any(v > 0 for v in monthly_values) else 1
        max_height = 160  # Maximum bar height in pixels
        
        # Find all chart-bar-wrapper divs (should be 12 total)
        wrapper_pattern = r'<div class="chart-bar-wrapper">\s*<div class="chart-bar" style="height:\s*\d+px;"[^>]*>.*?</div>\s*</div>'
        wrappers = list(re.finditer(wrapper_pattern, html_content, re.DOTALL))
        
        # Process each wrapper from right to left (reverse order) to avoid position shifts
        for i in reversed(range(min(len(wrappers), len(monthly_values)))):
            wrapper_match = wrappers[i]
            value = monthly_values[i]
            month = months[i]
            
            # Calculate proportional height
            height = int((value / max_value) * max_height) if max_value > 0 else 0
            
            # Create the new wrapper content
            if value > 0:
                new_wrapper = f'''<div class="chart-bar-wrapper">
                    <div class="chart-bar" style="height: {height}px;">
                        <span class="chart-bar-value">{int(value)}</span>
                    </div>
                </div>'''
            else:
                new_wrapper = f'''<div class="chart-bar-wrapper">
                    <div class="chart-bar" style="height: {height}px;"></div>
                </div>'''
            
            # Replace the wrapper
            html_content = html_content[:wrapper_match.start()] + new_wrapper + html_content[wrapper_match.end():]
        
        return html_content

def main(report_id: Optional[str] = None, test_mode: bool = False):
    """Main function for command line usage"""
    generator = ReportGenerator(test_mode=test_mode)
    
    if report_id:
        # Generate specific report
        result = generator.generate_and_deploy(report_id)
        if result:
            if test_mode:
                print(f"\n✓ Test report generated successfully: {result}")
                print(f"📁 Check templates/development/ for output files")
            else:
                print(f"\n✓ Report generated successfully: {result}")
        else:
            print("\n✗ Report generation failed")
    else:
        print("Usage: python report_generator.py <report_id> [--test]")
        print("Examples:")
        print("  python report_generator.py recABC123")
        print("  python report_generator.py recABC123 --test")
        print("")
        print("Options:")
        print("  --test    Run in test mode (saves to templates/development/)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        report_id = sys.argv[1]
        test_mode = "--test" in sys.argv
        main(report_id, test_mode)
    else:
        main()
