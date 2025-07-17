#!/usr/bin/env python3
"""
Headshot Sync Script - Weekly Batch Processing

This script:
1. Fetches all clients with headshots from Airtable
2. Downloads and stores headshots in GitHub repository
3. Creates a manifest to track processed images
4. Runs as a weekly cron job to pre-process all headshots

This separates headshot processing from report generation to prevent
GitHub deployment conflicts.
"""

import os
import json
import logging
import requests
import base64
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
BATCH_SIZE = 10
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MANIFEST_PATH = "assets/headshots/manifest.json"

class HeadshotSync:
    def __init__(self):
        if not AIRTABLE_API_KEY or not BASE_ID or not GITHUB_TOKEN or not GITHUB_REPO:
            raise ValueError("Missing required environment variables")
            
        self.airtable = Api(AIRTABLE_API_KEY)
        self.base_id = BASE_ID
        self.table = self.airtable.table(BASE_ID, 'Report_Variables')
        self.github_repo = GITHUB_REPO
        self.github_token = GITHUB_TOKEN
        self.manifest = {}
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.orphaned_count = 0  # Track orphaned images removed
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging to file and console"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_filename = f"headshot_sync_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = log_dir / log_filename
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_manifest(self):
        """Load existing manifest from GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/contents/{MANIFEST_PATH}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                content = response.json()
                manifest_data = base64.b64decode(content['content']).decode('utf-8')
                self.manifest = json.loads(manifest_data)
                self.logger.info(f"Loaded manifest with {len(self.manifest.get('headshots', {}))} entries")
            else:
                self.logger.info("No existing manifest found, creating new one")
                self.manifest = {
                    'last_sync': None,
                    'headshots': {}
                }
        except Exception as e:
            self.logger.error(f"Error loading manifest: {e}")
            self.manifest = {
                'last_sync': None,
                'headshots': {}
            }
            
    def save_manifest(self):
        """Save manifest to GitHub"""
        try:
            self.manifest['last_sync'] = datetime.now().isoformat()
            manifest_json = json.dumps(self.manifest, indent=2)
            
            url = f"https://api.github.com/repos/{self.github_repo}/contents/{MANIFEST_PATH}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Check if manifest exists to get SHA for update
            response = requests.get(url, headers=headers)
            data = {
                'message': f'Update headshot manifest - {datetime.now().strftime("%Y-%m-%d")}',
                'content': base64.b64encode(manifest_json.encode('utf-8')).decode('utf-8')
            }
            
            if response.status_code == 200:
                # Update existing file
                data['sha'] = response.json()['sha']
                response = requests.put(url, headers=headers, json=data)
            else:
                # Create new file
                response = requests.put(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                self.logger.info("Manifest saved successfully")
            else:
                self.logger.error(f"Failed to save manifest: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error saving manifest: {e}")
            
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Fetch all active clients with headshots from Client_Variables table"""
        try:
            self.logger.info("Fetching active clients from Client_Variables table...")
            
            # Use Client_Variables table instead of Report_Variables
            client_table = self.airtable.table(self.base_id, 'Client_Variables')
            
            # Filter for active clients only
            formula = '{Status (from Active Subscriptions)} != "canceled"'
            records = client_table.all(formula=formula)
            
            clients_with_headshots = []
            for record in records:
                fields = record.get('fields', {})
                client_name = fields.get('Name')  # Changed from 'client_name' to 'Name'
                headshot_data = fields.get('Headshots')  # Changed from 'client_headshot' to 'Headshots'
                status = fields.get('Status (from Active Subscriptions)', 'unknown')
                
                if client_name and headshot_data:
                    clients_with_headshots.append({
                        'id': record['id'],
                        'client_name': client_name,
                        'headshot_data': headshot_data,
                        'last_modified': record.get('createdTime'),
                        'status': status
                    })
                    
            self.logger.info(f"Found {len(clients_with_headshots)} active clients with headshots")
            return clients_with_headshots
            
        except Exception as e:
            self.logger.error(f"Error fetching clients: {e}")
            return []
            
    def _extract_image_url(self, attachment_data: Any) -> str:
        """Extract the full-size image URL from Airtable attachment data"""
        try:
            if isinstance(attachment_data, dict):
                url = attachment_data.get('url')
                if url:
                    return url
            elif isinstance(attachment_data, list) and attachment_data:
                first_attachment = attachment_data[0]
                if isinstance(first_attachment, dict):
                    url = first_attachment.get('url')
                    if url:
                        return url
            elif isinstance(attachment_data, str):
                try:
                    parsed = json.loads(attachment_data)
                    return self._extract_image_url(parsed)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            self.logger.warning(f"Could not extract image URL from {attachment_data}: {e}")
        
        return ""
        
    def _create_safe_filename(self, client_name: str) -> str:
        """Create safe filename from client name"""
        safe_name = re.sub(r'[^a-zA-Z0-9-]', '', client_name.replace(' ', '-').lower())
        return f"{safe_name}-headshot.jpg"
        
    def _validate_image(self, image_data: bytes) -> bool:
        """Validate image size and basic format"""
        if len(image_data) > MAX_IMAGE_SIZE:
            return False
            
        # Basic image format validation
        valid_headers = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'RIFF',  # WebP/other RIFF formats
            b'GIF87a',  # GIF87a
            b'GIF89a'   # GIF89a
        ]
        
        for header in valid_headers:
            if image_data.startswith(header):
                return True
                
        return False
        
    def process_client_headshot(self, client: Dict[str, Any]) -> Dict[str, Any]:
        """Download and prepare individual headshot for bulk processing"""
        try:
            client_name = client['client_name']
            headshot_data = client['headshot_data']
            
            # Extract image URL
            image_url = self._extract_image_url(headshot_data)
            if not image_url:
                self.logger.warning(f"No image URL found for {client_name}")
                return {'status': 'failed', 'reason': 'No image URL'}
                
            # Create filename
            filename = self._create_safe_filename(client_name)
            file_path = f"assets/headshots/{filename}"
            
            # Check if we need to update (skip if unchanged)
            manifest_entry = self.manifest.get('headshots', {}).get(client_name, {})
            if (manifest_entry.get('url') == image_url and 
                manifest_entry.get('processed_date')):
                self.logger.info(f"Skipping {client_name} - unchanged")
                return {'status': 'skipped', 'client_name': client_name}
                
            # Download image
            self.logger.info(f"Processing headshot for {client_name}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Validate image
            if not self._validate_image(response.content):
                self.logger.error(f"Invalid image format or size for {client_name}")
                return {'status': 'failed', 'reason': 'Invalid image format'}
                
            # Return image data for bulk processing
            return {
                'status': 'ready',
                'client_name': client_name,
                'file_path': file_path,
                'image_data': response.content,
                'image_url': image_url,
                'filename': filename,
                'file_size': len(response.content)
            }
                
        except Exception as e:
            self.logger.error(f"Error processing headshot for {client.get('client_name', 'unknown')}: {e}")
            return {'status': 'failed', 'reason': str(e)}
            
    def _store_images_bulk(self, pending_images: List[Dict]) -> bool:
        """Store multiple images in GitHub repository using a single commit"""
        if not pending_images:
            return True
            
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get current branch SHA
            ref_url = f"https://api.github.com/repos/{self.github_repo}/git/refs/heads/main"
            ref_response = requests.get(ref_url, headers=headers)
            ref_response.raise_for_status()
            base_sha = ref_response.json()['object']['sha']
            
            # Create blobs for each image
            blobs = []
            for image_data in pending_images:
                blob_url = f"https://api.github.com/repos/{self.github_repo}/git/blobs"
                blob_data = {
                    'content': base64.b64encode(image_data['image_data']).decode('utf-8'),
                    'encoding': 'base64'
                }
                blob_response = requests.post(blob_url, headers=headers, json=blob_data)
                blob_response.raise_for_status()
                blob_sha = blob_response.json()['sha']
                
                blobs.append({
                    'path': image_data['file_path'],
                    'sha': blob_sha,
                    'client_name': image_data['client_name']
                })
            
            # Create tree
            tree_url = f"https://api.github.com/repos/{self.github_repo}/git/trees"
            tree_data = {
                'base_tree': base_sha,
                'tree': [
                    {
                        'path': blob['path'],
                        'mode': '100644',
                        'type': 'blob',
                        'sha': blob['sha']
                    } for blob in blobs
                ]
            }
            tree_response = requests.post(tree_url, headers=headers, json=tree_data)
            tree_response.raise_for_status()
            tree_sha = tree_response.json()['sha']
            
            # Create commit
            commit_url = f"https://api.github.com/repos/{self.github_repo}/git/commits"
            client_names = [blob['client_name'] for blob in blobs]
            commit_message = f"Bulk update headshots for {len(client_names)} clients"
            if len(client_names) <= 3:
                commit_message += f": {', '.join(client_names)}"
            
            commit_data = {
                'message': commit_message,
                'tree': tree_sha,
                'parents': [base_sha]
            }
            commit_response = requests.post(commit_url, headers=headers, json=commit_data)
            commit_response.raise_for_status()
            commit_sha = commit_response.json()['sha']
            
            # Update branch reference
            ref_update_data = {
                'sha': commit_sha,
                'force': False
            }
            ref_update_response = requests.patch(ref_url, headers=headers, json=ref_update_data)
            ref_update_response.raise_for_status()
            
            self.logger.info(f"Bulk commit successful: {len(pending_images)} images in 1 commit")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in bulk commit: {e}")
            return False
            
    def cleanup_orphaned_images(self):
        """Remove images for deleted clients"""
        try:
            self.logger.info("Checking for orphaned images...")
            
            # Get current clients
            current_clients = {client['client_name'] for client in self.get_all_clients()}
            
            # Check manifest for clients no longer in Airtable
            manifest_clients = set(self.manifest.get('headshots', {}).keys())
            orphaned_clients = manifest_clients - current_clients
            
            for client_name in orphaned_clients:
                self.logger.info(f"Removing orphaned image for {client_name}")
                filename = self.manifest['headshots'][client_name]['filename']
                file_path = f"assets/headshots/{filename}"
                
                # Delete from GitHub
                url = f"https://api.github.com/repos/{self.github_repo}/contents/{file_path}"
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                # Get file SHA
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    sha = response.json()['sha']
                    
                    # Delete file
                    data = {
                        'message': f'Remove orphaned headshot for {client_name}',
                        'sha': sha
                    }
                    
                    delete_response = requests.delete(url, headers=headers, json=data)
                    if delete_response.status_code == 200:
                        self.logger.info(f"Successfully removed orphaned image for {client_name}")
                        self.orphaned_count += 1
                    else:
                        self.logger.error(f"Failed to remove orphaned image for {client_name}")
                        
                # Remove from manifest
                del self.manifest['headshots'][client_name]
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    def sync_all_headshots(self) -> Dict[str, Any]:
        """Main entry point - sync all headshots with bulk commits"""
        try:
            self.logger.info("Starting headshot sync process...")
            
            # Load existing manifest
            self.load_manifest()
            
            # Get all clients with headshots
            clients = self.get_all_clients()
            
            if not clients:
                self.logger.warning("No clients with headshots found")
                return {
                    'processed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'total': 0
                }
                
            # Process all clients and collect images for bulk upload
            pending_images = []
            
            for client in clients:
                result = self.process_client_headshot(client)
                
                if result['status'] == 'ready':
                    pending_images.append(result)
                elif result['status'] == 'skipped':
                    self.skipped_count += 1
                elif result['status'] == 'failed':
                    self.failed_count += 1
                    
            # Bulk upload all pending images in a single commit
            if pending_images:
                self.logger.info(f"Bulk uploading {len(pending_images)} images...")
                if self._store_images_bulk(pending_images):
                    # Update manifest for all successfully uploaded images
                    if 'headshots' not in self.manifest:
                        self.manifest['headshots'] = {}
                        
                    for image_data in pending_images:
                        client_name = image_data['client_name']
                        self.manifest['headshots'][client_name] = {
                            'filename': image_data['filename'],
                            'url': image_data['image_url'],
                            'processed_date': datetime.now().isoformat(),
                            'file_size': image_data['file_size'],
                            'github_url': f"https://app.agentinsider.co/assets/headshots/{image_data['filename']}"
                        }
                        self.processed_count += 1
                        
                    self.logger.info(f"Successfully bulk uploaded {len(pending_images)} images")
                else:
                    self.logger.error("Bulk upload failed")
                    self.failed_count += len(pending_images)
                    
            # Cleanup orphaned images
            self.cleanup_orphaned_images()
            
            # Save manifest only if there were changes
            changes_made = self.processed_count > 0 or self.failed_count > 0 or self.orphaned_count > 0
            if changes_made:
                self.save_manifest()
                self.logger.info(f"Manifest updated due to changes (processed: {self.processed_count}, failed: {self.failed_count}, orphaned: {self.orphaned_count})")
            else:
                self.logger.info("No changes detected, skipping manifest update to avoid unnecessary deployments")
            
            # Return summary
            results = {
                'processed': self.processed_count,
                'failed': self.failed_count,
                'skipped': self.skipped_count,
                'orphaned': self.orphaned_count,
                'total': len(clients)
            }
            
            self.logger.info(f"Sync completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in sync_all_headshots: {e}")
            return {
                'processed': self.processed_count,
                'failed': self.failed_count,
                'skipped': self.skipped_count,
                'total': 0,
                'error': str(e)
            }

def main():
    """Main function for CLI usage"""
    try:
        sync = HeadshotSync()
        results = sync.sync_all_headshots()
        
        print(f"\n{'='*50}")
        print(f"HEADSHOT SYNC RESULTS")
        print(f"{'='*50}")
        print(f"Total clients: {results['total']}")
        print(f"Processed: {results['processed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Failed: {results['failed']}")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} headshots failed to process")
            exit(1)
        else:
            print(f"\n✅ All headshots processed successfully!")
            exit(0)
            
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
