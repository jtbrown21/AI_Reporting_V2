"""
Webhook Server for n8n Integration

This Flask server provides webhook endpoints for n8n workflows to trigger
report generation and deployment.
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from report_generator import ReportGenerator
from calculation_engine import main as run_calculation_engine
import threading
import time

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key')

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting webhook server on port {port}")
    print(f"Available endpoints:")
    print(f"  GET  /health - Health check")
    print(f"  POST /webhook/calculation-and-report - Execute full calculation and report generation")
    print(f"  POST /webhook/calculation-only - Run calculation engine only")
    print(f"  POST /webhook/report-only - Generate and deploy report only")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
