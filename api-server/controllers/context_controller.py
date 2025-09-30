"""
Context Controller - Business logic for context management
"""

import time
import uuid
import json
import os
from typing import Dict, Any, List
from datetime import datetime


class ContextController:
    """Controller for context management operations"""
    
    # In-memory storage for demo purposes
    # In production, this would use a proper database
    _repositories = []
    _mcp_resources = []
    
    @classmethod
    def get_repositories(cls) -> Dict[str, Any]:
        """
        Get all connected repositories
        
        Returns:
            Dict containing repositories list
        """
        return {
            "status": "success",
            "repositories": cls._repositories,
            "count": len(cls._repositories),
            "timestamp": int(time.time() * 1000)
        }
    
    @classmethod
    def add_repository(cls, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new repository to context
        
        Args:
            repo_data: Repository configuration data
            
        Returns:
            Dict containing operation result
        """
        try:
            # Generate unique ID
            repo_id = str(uuid.uuid4())
            
            # Create repository record
            repository = {
                "id": repo_id,
                "name": repo_data["name"],
                "url": repo_data["url"],
                "branch": repo_data.get("branch", "main"),
                "access_token": repo_data.get("accessToken", ""),
                "created_at": datetime.now().isoformat(),
                "status": "connected"
            }
            
            # Add to storage
            cls._repositories.append(repository)
            
            # TODO: In production, trigger repository cloning and RAG indexing
            # This would involve:
            # 1. Clone the repository using git
            # 2. Extract code files and documentation
            # 3. Send to embedding service for RAG indexing
            # 4. Store document IDs for context retrieval
            
            return {
                "status": "success",
                "repository": repository,
                "message": f"Repository '{repo_data['name']}' added successfully",
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to add repository: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def remove_repository(cls, repo_id: str) -> Dict[str, Any]:
        """
        Remove repository from context
        
        Args:
            repo_id: Repository ID to remove
            
        Returns:
            Dict containing operation result
        """
        try:
            # Find and remove repository
            original_count = len(cls._repositories)
            cls._repositories = [repo for repo in cls._repositories if repo["id"] != repo_id]
            
            if len(cls._repositories) < original_count:
                # TODO: In production, also remove from RAG index
                # This would involve:
                # 1. Find all document IDs associated with this repository
                # 2. Remove documents from embedding service
                # 3. Clean up any temporary files
                
                return {
                    "status": "success",
                    "message": "Repository removed successfully",
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": "Repository not found",
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to remove repository: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def get_mcp_resources(cls) -> Dict[str, Any]:
        """
        Get all MCP resources in context
        
        Returns:
            Dict containing MCP resources list
        """
        return {
            "status": "success",
            "resources": cls._mcp_resources,
            "count": len(cls._mcp_resources),
            "timestamp": int(time.time() * 1000)
        }
    
    @classmethod
    def add_mcp_resource(cls, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add MCP resource to context
        
        Args:
            resource_data: MCP resource configuration data
            
        Returns:
            Dict containing operation result
        """
        try:
            # Generate unique ID
            resource_id = str(uuid.uuid4())
            
            # Create MCP resource record
            mcp_resource = {
                "id": resource_id,
                "provider_id": resource_data["provider_id"],
                "token_id": resource_data["token_id"],
                "resource_id": resource_data["resource_id"],
                "resource_name": resource_data["resource_name"],
                "resource_type": resource_data["resource_type"],
                "resource_data": resource_data.get("resource_data", {}),
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Add to storage
            cls._mcp_resources.append(mcp_resource)
            
            # TODO: In production, trigger resource processing and RAG indexing
            # This would involve:
            # 1. Use MCP provider to fetch resource content
            # 2. Process content based on resource type (repository, database, document)
            # 3. Send processed content to embedding service for RAG indexing
            # 4. Store document IDs for context retrieval
            
            return {
                "status": "success",
                "resource": mcp_resource,
                "message": f"MCP resource '{resource_data['resource_name']}' added successfully",
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to add MCP resource: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def remove_mcp_resource(cls, resource_id: str) -> Dict[str, Any]:
        """
        Remove MCP resource from context
        
        Args:
            resource_id: MCP resource ID to remove
            
        Returns:
            Dict containing operation result
        """
        try:
            # Find and remove MCP resource
            original_count = len(cls._mcp_resources)
            cls._mcp_resources = [res for res in cls._mcp_resources if res["id"] != resource_id]
            
            if len(cls._mcp_resources) < original_count:
                # TODO: In production, also remove from RAG index
                # This would involve:
                # 1. Find all document IDs associated with this MCP resource
                # 2. Remove documents from embedding service
                # 3. Clean up any cached data
                
                return {
                    "status": "success",
                    "message": "MCP resource removed successfully",
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": "MCP resource not found",
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to remove MCP resource: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
