"""
GitHub MCP Service - MCP server implementation for GitHub operations
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
import git
import tempfile
import os
import shutil

from services.github_oauth_service import GitHubOAuthService


class GitHubMCPService:
    """MCP service for GitHub operations using OAuth authentication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.oauth_service = GitHubOAuthService()
        
        # Define available tools
        self.tools = [
            {
                "name": "list_repositories",
                "description": "List user's GitHub repositories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"},
                        "type": {"type": "string", "enum": ["all", "owner", "member"], "default": "owner"},
                        "sort": {"type": "string", "enum": ["created", "updated", "pushed", "full_name"], "default": "updated"},
                        "per_page": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30}
                    },
                    "required": ["token_id"]
                }
            },
            {
                "name": "get_repository",
                "description": "Get detailed information about a specific repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"},
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"}
                    },
                    "required": ["token_id", "owner", "repo"]
                }
            },
            {
                "name": "clone_repository",
                "description": "Clone a repository to temporary storage for analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"},
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "branch": {"type": "string", "description": "Branch to clone", "default": "main"}
                    },
                    "required": ["token_id", "owner", "repo"]
                }
            },
            {
                "name": "get_repository_contents",
                "description": "Get contents of a repository directory or file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"},
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "path": {"type": "string", "description": "Path to directory or file", "default": ""},
                        "ref": {"type": "string", "description": "Branch, tag, or commit SHA", "default": "main"}
                    },
                    "required": ["token_id", "owner", "repo"]
                }
            },
            {
                "name": "search_repositories",
                "description": "Search GitHub repositories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"},
                        "query": {"type": "string", "description": "Search query"},
                        "sort": {"type": "string", "enum": ["stars", "forks", "help-wanted-issues", "updated"], "default": "stars"},
                        "order": {"type": "string", "enum": ["desc", "asc"], "default": "desc"},
                        "per_page": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30}
                    },
                    "required": ["token_id", "query"]
                }
            },
            {
                "name": "get_user_profile",
                "description": "Get authenticated user's GitHub profile",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "OAuth token ID"}
                    },
                    "required": ["token_id"]
                }
            }
        ]
        
        # Define available resources
        self.resources = [
            {
                "uri": "github://repositories",
                "name": "User Repositories",
                "description": "Access to user's GitHub repositories",
                "mimeType": "application/json"
            },
            {
                "uri": "github://profile",
                "name": "User Profile",
                "description": "Access to user's GitHub profile information",
                "mimeType": "application/json"
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools"""
        return self.tools
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get available resources"""
        return self.resources
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GitHub tool
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Dict with execution result
        """
        try:
            if tool_name == "list_repositories":
                return self._list_repositories(arguments)
            elif tool_name == "get_repository":
                return self._get_repository(arguments)
            elif tool_name == "clone_repository":
                return self._clone_repository(arguments)
            elif tool_name == "get_repository_contents":
                return self._get_repository_contents(arguments)
            elif tool_name == "search_repositories":
                return self._search_repositories(arguments)
            elif tool_name == "get_user_profile":
                return self._get_user_profile(arguments)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Tool execution failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}"
            }
    
    def _get_github_headers(self, token_id: str) -> Optional[Dict[str, str]]:
        """Get GitHub API headers with authentication"""
        token_info = self.oauth_service.get_token_info(token_id)
        if not token_info:
            return None
        
        return {
            'Authorization': f'Bearer {token_info["access_token"]}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'iChat-MCP-Service/1.0'
        }
    
    def _list_repositories(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List user's repositories"""
        token_id = arguments.get('token_id')
        repo_type = arguments.get('type', 'owner')
        sort = arguments.get('sort', 'updated')
        per_page = arguments.get('per_page', 30)
        
        headers = self._get_github_headers(token_id)
        if not headers:
            return {"status": "error", "error": "Invalid token ID"}
        
        params = {
            'type': repo_type,
            'sort': sort,
            'per_page': per_page
        }
        
        response = requests.get(
            'https://api.github.com/user/repos',
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            repos = response.json()
            return {
                "status": "success",
                "repositories": [
                    {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "private": repo["private"],
                        "html_url": repo["html_url"],
                        "clone_url": repo["clone_url"],
                        "language": repo.get("language"),
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "updated_at": repo["updated_at"]
                    }
                    for repo in repos
                ]
            }
        else:
            return {
                "status": "error",
                "error": f"GitHub API error: {response.status_code}"
            }
    
    def _get_repository(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository details"""
        token_id = arguments.get('token_id')
        owner = arguments.get('owner')
        repo = arguments.get('repo')
        
        headers = self._get_github_headers(token_id)
        if not headers:
            return {"status": "error", "error": "Invalid token ID"}
        
        response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            repo_data = response.json()
            return {
                "status": "success",
                "repository": {
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description", ""),
                    "private": repo_data["private"],
                    "html_url": repo_data["html_url"],
                    "clone_url": repo_data["clone_url"],
                    "language": repo_data.get("language"),
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"],
                    "size": repo_data["size"],
                    "default_branch": repo_data["default_branch"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "topics": repo_data.get("topics", [])
                }
            }
        else:
            return {
                "status": "error",
                "error": f"Repository not found or access denied: {response.status_code}"
            }

    def _clone_repository(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Clone repository to temporary storage"""
        token_id = arguments.get('token_id')
        owner = arguments.get('owner')
        repo = arguments.get('repo')
        branch = arguments.get('branch', 'main')

        token_info = self.oauth_service.get_token_info(token_id)
        if not token_info:
            return {"status": "error", "error": "Invalid token ID"}

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"github_{owner}_{repo}_")

            # Build clone URL with token
            clone_url = f"https://{token_info['access_token']}@github.com/{owner}/{repo}.git"

            # Clone repository
            repo_obj = git.Repo.clone_from(clone_url, temp_dir, branch=branch)

            # Get repository info
            repo_info = {
                "local_path": temp_dir,
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "commit_sha": repo_obj.head.commit.hexsha,
                "commit_message": repo_obj.head.commit.message.strip(),
                "commit_author": str(repo_obj.head.commit.author),
                "commit_date": repo_obj.head.commit.committed_datetime.isoformat()
            }

            return {
                "status": "success",
                "repository_info": repo_info,
                "message": f"Repository cloned to {temp_dir}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to clone repository: {str(e)}"
            }

    def _get_repository_contents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository contents"""
        token_id = arguments.get('token_id')
        owner = arguments.get('owner')
        repo = arguments.get('repo')
        path = arguments.get('path', '')
        ref = arguments.get('ref', 'main')

        headers = self._get_github_headers(token_id)
        if not headers:
            return {"status": "error", "error": "Invalid token ID"}

        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        params = {'ref': ref} if ref != 'main' else {}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            contents = response.json()

            if isinstance(contents, list):
                # Directory contents
                return {
                    "status": "success",
                    "type": "directory",
                    "contents": [
                        {
                            "name": item["name"],
                            "path": item["path"],
                            "type": item["type"],
                            "size": item.get("size", 0),
                            "download_url": item.get("download_url")
                        }
                        for item in contents
                    ]
                }
            else:
                # Single file
                return {
                    "status": "success",
                    "type": "file",
                    "file": {
                        "name": contents["name"],
                        "path": contents["path"],
                        "size": contents["size"],
                        "content": contents.get("content", ""),
                        "encoding": contents.get("encoding", ""),
                        "download_url": contents.get("download_url")
                    }
                }
        else:
            return {
                "status": "error",
                "error": f"Failed to get contents: {response.status_code}"
            }

    def _search_repositories(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search repositories"""
        token_id = arguments.get('token_id')
        query = arguments.get('query')
        sort = arguments.get('sort', 'stars')
        order = arguments.get('order', 'desc')
        per_page = arguments.get('per_page', 30)

        headers = self._get_github_headers(token_id)
        if not headers:
            return {"status": "error", "error": "Invalid token ID"}

        params = {
            'q': query,
            'sort': sort,
            'order': order,
            'per_page': per_page
        }

        response = requests.get(
            'https://api.github.com/search/repositories',
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            search_results = response.json()
            return {
                "status": "success",
                "total_count": search_results["total_count"],
                "repositories": [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "html_url": repo["html_url"],
                        "language": repo.get("language"),
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "updated_at": repo["updated_at"]
                    }
                    for repo in search_results["items"]
                ]
            }
        else:
            return {
                "status": "error",
                "error": f"Search failed: {response.status_code}"
            }

    def _get_user_profile(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get user profile"""
        token_id = arguments.get('token_id')

        headers = self._get_github_headers(token_id)
        if not headers:
            return {"status": "error", "error": "Invalid token ID"}

        response = requests.get(
            'https://api.github.com/user',
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            user_data = response.json()
            return {
                "status": "success",
                "profile": {
                    "login": user_data["login"],
                    "name": user_data.get("name", ""),
                    "email": user_data.get("email", ""),
                    "bio": user_data.get("bio", ""),
                    "company": user_data.get("company", ""),
                    "location": user_data.get("location", ""),
                    "public_repos": user_data["public_repos"],
                    "followers": user_data["followers"],
                    "following": user_data["following"],
                    "created_at": user_data["created_at"],
                    "avatar_url": user_data["avatar_url"],
                    "html_url": user_data["html_url"]
                }
            }
        else:
            return {
                "status": "error",
                "error": f"Failed to get profile: {response.status_code}"
            }
