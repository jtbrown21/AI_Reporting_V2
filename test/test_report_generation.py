"""
Test Suite for Report Generation System

This script tests the various components of the report generation system.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

class ReportGenerationTester:
    """Test suite for the report generation system"""
    
    def __init__(self):
        self.webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000')
        self.webhook_secret = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret')
        self.test_report_id = os.environ.get('TEST_REPORT_ID', 'recABC123')
        
    def test_health_check(self):
        """Test the health check endpoint"""
        print("Testing health check endpoint...")
        try:
            response = requests.get(f"{self.webhook_url}/health")
            if response.status_code == 200:
                print("✓ Health check passed")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def test_webhook_generate_report_sync(self):
        """Test synchronous report generation webhook"""
        print("Testing synchronous report generation...")
        try:
            headers = {
                'X-Webhook-Secret': self.webhook_secret,
                'Content-Type': 'application/json'
            }
            data = {
                'report_id': self.test_report_id
            }
            
            response = requests.post(
                f"{self.webhook_url}/webhook/generate-report-sync",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Sync report generation passed")
                print(f"  Report URL: {result.get('url', 'N/A')}")
                return True
            else:
                print(f"✗ Sync report generation failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Sync report generation error: {e}")
            return False
    
    def test_webhook_generate_report_async(self):
        """Test asynchronous report generation webhook"""
        print("Testing asynchronous report generation...")
        try:
            headers = {
                'X-Webhook-Secret': self.webhook_secret,
                'Content-Type': 'application/json'
            }
            data = {
                'report_id': self.test_report_id
            }
            
            response = requests.post(
                f"{self.webhook_url}/webhook/generate-report",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Async report generation started")
                print(f"  Message: {result.get('message', 'N/A')}")
                return True
            else:
                print(f"✗ Async report generation failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Async report generation error: {e}")
            return False
    
    def test_webhook_calculation_only(self):
        """Test calculation-only webhook"""
        print("Testing calculation-only webhook...")
        try:
            headers = {
                'X-Webhook-Secret': self.webhook_secret,
                'Content-Type': 'application/json'
            }
            data = {
                'report_id': self.test_report_id
            }
            
            response = requests.post(
                f"{self.webhook_url}/webhook/calculation-only",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Calculation-only webhook passed")
                print(f"  Message: {result.get('message', 'N/A')}")
                return True
            else:
                print(f"✗ Calculation-only webhook failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Calculation-only webhook error: {e}")
            return False
    
    def test_webhook_security(self):
        """Test webhook security (invalid secret)"""
        print("Testing webhook security...")
        try:
            headers = {
                'X-Webhook-Secret': 'invalid-secret',
                'Content-Type': 'application/json'
            }
            data = {
                'report_id': self.test_report_id
            }
            
            response = requests.post(
                f"{self.webhook_url}/webhook/generate-report-sync",
                headers=headers,
                json=data
            )
            
            if response.status_code == 401:
                print("✓ Webhook security test passed (unauthorized)")
                return True
            else:
                print(f"✗ Webhook security test failed: {response.status_code}")
                print("  Security check should have rejected invalid secret")
                return False
        except Exception as e:
            print(f"✗ Webhook security test error: {e}")
            return False
    
    def test_local_report_generation(self):
        """Test local report generation"""
        print("Testing local report generation...")
        try:
            from report_generator import ReportGenerator
            
            generator = ReportGenerator()
            report_data = generator.get_report_data(self.test_report_id)
            
            if report_data:
                print("✓ Local report generation test passed")
                print(f"  Retrieved data for report: {self.test_report_id}")
                return True
            else:
                print("✗ Local report generation test failed")
                print(f"  Could not retrieve data for report: {self.test_report_id}")
                return False
        except Exception as e:
            print(f"✗ Local report generation test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("REPORT GENERATION SYSTEM TEST SUITE")
        print("="*70)
        print(f"Webhook URL: {self.webhook_url}")
        print(f"Test Report ID: {self.test_report_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        results = {
            "health_check": self.test_health_check(),
            "webhook_security": self.test_webhook_security(),
            "local_report_generation": self.test_local_report_generation(),
            "webhook_calculation_only": self.test_webhook_calculation_only(),
            "webhook_async": self.test_webhook_generate_report_async(),
            "webhook_sync": self.test_webhook_generate_report_sync()
        }
        
        print()
        print("="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name:<30} {status}")
        
        print()
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("❌ Some tests failed. Check the output above for details.")
        
        return results

def main():
    """Run the test suite"""
    tester = ReportGenerationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
