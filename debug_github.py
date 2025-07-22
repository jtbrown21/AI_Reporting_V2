#!/usr/bin/env python3
"""
Debug script to test GitHub authentication on Railway
Add this as a route to webhook_server.py to test authentication directly on Railway
"""

import os
import github
from flask import jsonify

def debug_github_auth():
    """Debug GitHub authentication - returns JSON response"""
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
            return result
            
        if not github_repo:
            result["error"] = "GITHUB_REPO not set" 
            return result
        
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
    
    return result
