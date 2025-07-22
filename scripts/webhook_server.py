"""
Webhook Server for n8n Integration

This Flask server provides webhook endpoints for n8n workflows to trigger
report generation and deployment.
"""

from flask import Flask, request, jsonify
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import time
import github

# Add the scripts directory to the path for imports
sys.path.append(str(Path(__file__).parent))

from report_generator import ReportGenerator
from calculation_engine import main as run_calculation_engine
import threading

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key')

# Request deduplication cache
request_cache = {}
CACHE_TTL = 300  # 5 minutes

def is_duplicate_request(report_id: str, endpoint: str) -> bool:
    """Check if this is a duplicate request within the cache TTL"""
    cache_key = f"{endpoint}:{report_id}"
    current_time = time.time()
    
    # Clean expired entries
    expired_keys = [key for key, timestamp in request_cache.items() 
                   if current_time - timestamp > CACHE_TTL]
    for key in expired_keys:
        del request_cache[key]
    
    # Check if request is duplicate
    if cache_key in request_cache:
        return True
    
    # Mark request as processed
    request_cache[cache_key] = current_time
    return False

class ReportProcessor:
    """Background processor for report generation"""
    
    def __init__(self):
        self.generator = ReportGenerator()
    
    def process_report(self, report_id: str):
        """Process a report in the background"""
        try:
            print(f"Starting report processing for {report_id}")
            
            # Step 1: Run calculation engine
            print("Running calculation engine...")
            run_calculation_engine(report_id)
            
            # Step 2: Generate and deploy report
            print("Generating and deploying report...")
            url = self.generator.generate_and_deploy(report_id)
            
            if url:
                print(f"Report generated successfully: {url}")
                return {"success": True, "url": url}
            else:
                print("Report generation failed")
                return {"success": False, "error": "Report generation failed"}
                
        except Exception as e:
            print(f"Error processing report {report_id}: {e}")
            return {"success": False, "error": str(e)}

processor = ReportProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "report-generator-webhook"
    })

@app.route('/debug/github', methods=['GET'])
def debug_github_auth():
    """Debug GitHub authentication endpoint"""
    try:
        # Get environment variables
        github_token = os.environ.get('GITHUB_TOKEN')
        github_repo = os.environ.get('GITHUB_REPO')
        
        result = {
            "environment_check": {
                "GITHUB_TOKEN": "Set" if github_token else "Not set",
                "GITHUB_TOKEN_length": len(github_token) if github_token else 0,
                "GITHUB_TOKEN_starts_with": github_token[:15] + "..." if github_token else "None",
                "GITHUB_REPO": github_repo or "Not set"
            }
        }
        
        if not github_token:
            result["error"] = "GITHUB_TOKEN not set"
            return jsonify(result)
            
        if not github_repo:
            result["error"] = "GITHUB_REPO not set"
            return jsonify(result)
        
        # Test GitHub authentication
        try:
            g = github.Github(github_token)
            user = g.get_user()
            
            result["github_auth"] = {
                "authenticated_user": user.login,
                "user_id": user.id,
                "user_type": user.type
            }
            
            # Test repository access
            try:
                repo = g.get_repo(github_repo)
                result["repository_access"] = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "permissions": {
                        "push": repo.permissions.push,
                        "pull": repo.permissions.pull,
                        "admin": repo.permissions.admin
                    },
                    "default_branch": repo.default_branch
                }
                
                # Test rate limit
                rate_limit = g.get_rate_limit()
                result["rate_limit"] = {
                    "remaining": rate_limit.core.remaining,
                    "limit": rate_limit.core.limit,
                    "reset_time": rate_limit.core.reset.isoformat()
                }
                
                result["status"] = "SUCCESS"
                
            except github.UnknownObjectException as e:
                result["error"] = f"Repository not found or no access: {e}"
            except Exception as e:
                result["error"] = f"Repository access error: {e}"
                
        except github.BadCredentialsException as e:
            result["error"] = f"Bad credentials: {e}"
        except github.RateLimitExceededException as e:
            result["error"] = f"Rate limit exceeded: {e}"
        except Exception as e:
            result["error"] = f"GitHub API error: {e}"
            
    except Exception as e:
        result = {"error": f"Unexpected error: {e}"}
    
    return jsonify(result)

@app.route('/webhook/calculation-and-report', methods=['POST'])
def calculation_and_report_webhook():
    """Execute full calculation and report generation"""
    try:
        # Verify webhook secret
        secret = request.headers.get('X-Webhook-Secret')
        if secret != WEBHOOK_SECRET:
            return jsonify({"error": "Invalid webhook secret"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract report ID
        report_id = data.get('report_id')
        if not report_id:
            return jsonify({"error": "report_id is required"}), 400
        
        # Check for duplicate request
        if is_duplicate_request(report_id, 'calculation-and-report'):
            return jsonify({
                "success": True,
                "message": "Request already processed (duplicate detected)",
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            })
        
        # Process report synchronously (calculation + report generation)
        result = processor.process_report(report_id)
        
        return jsonify({
            "success": result["success"],
            "report_id": report_id,
            "url": result.get("url"),
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/webhook/report-only', methods=['POST'])
def report_only_webhook():
    """Generate and deploy report only (assumes calculation is done)"""
    try:
        # Verify webhook secret
        secret = request.headers.get('X-Webhook-Secret')
        if secret != WEBHOOK_SECRET:
            return jsonify({"error": "Invalid webhook secret"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract report ID
        report_id = data.get('report_id')
        if not report_id:
            return jsonify({"error": "report_id is required"}), 400
        
        # Check for duplicate request
        if is_duplicate_request(report_id, 'report-only'):
            return jsonify({
                "success": True,
                "message": "Request already processed (duplicate detected)",
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate and deploy report only
        try:
            url = processor.generator.generate_and_deploy(report_id)
            if url:
                return jsonify({
                    "success": True,
                    "url": url,
                    "report_id": report_id,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Report generation and deployment failed",
                    "report_id": report_id,
                    "timestamp": datetime.now().isoformat()
                }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/webhook/calculation-only', methods=['POST'])
def calculation_only_webhook():
    """Webhook endpoint for running calculation engine only"""
    try:
        # Verify webhook secret
        secret = request.headers.get('X-Webhook-Secret')
        if secret != WEBHOOK_SECRET:
            return jsonify({"error": "Invalid webhook secret"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract report ID
        report_id = data.get('report_id')
        if not report_id:
            return jsonify({"error": "report_id is required"}), 400
        
        # Check for duplicate request
        if is_duplicate_request(report_id, 'calculation-only'):
            return jsonify({
                "success": True,
                "message": "Request already processed (duplicate detected)",
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            })
        
        # Run calculation engine only
        try:
            run_calculation_engine(report_id)
            return jsonify({
                "success": True,
                "message": "Calculation engine completed",
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "report_id": report_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/webhook/debug', methods=['POST'])
def debug_webhook():
    """Debug endpoint to test GitHub authentication"""
    try:
        # Verify webhook secret
        secret = request.headers.get('X-Webhook-Secret')
        if secret != WEBHOOK_SECRET:
            return jsonify({"error": "Invalid webhook secret"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract action and repository from payload
        action = data.get('action')
        repository = data.get('repository', {}).get('name')
        
        if action == 'opened' and repository:
            # Simulate processing for opened issue or pull request
            return jsonify({
                "success": True,
                "message": "Debug webhook received",
                "action": action,
                "repository": repository,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Unsupported action or missing repository",
                "timestamp": datetime.now().isoformat()
            }), 400
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting webhook server on port {port}")
    print(f"Available endpoints:")
    print(f"  GET  /health - Health check")
    print(f"  POST /webhook/calculation-and-report - Execute full calculation and report generation")
    print(f"  POST /webhook/calculation-only - Run calculation engine only")
    print(f"  POST /webhook/report-only - Generate and deploy report only")
    print(f"  POST /webhook/debug - Debug endpoint for GitHub authentication")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
