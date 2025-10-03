"""
Context Controller - Business logic for context management
"""

import time
import uuid
import json
import os
import sqlite3
from typing import Dict, Any, List
from datetime import datetime


class ContextController:
    """Controller for context management operations"""

    def __init__(self):
        self.db_path = "data/context.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for persistent context storage"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Customer context table - stores all context resources per customer
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT NOT NULL DEFAULT 'default',
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,  -- 'repository', 'remote_host', 'document'
                    resource_name TEXT NOT NULL,
                    resource_data TEXT NOT NULL,  -- JSON data
                    provider_id TEXT,  -- 'github', 'remote_host', 'manual'
                    token_id TEXT,     -- MCP token reference
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, resource_id)
                )
            ''')

            # Index for faster customer queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_customer_context_customer_id
                ON customer_context(customer_id, is_active)
            ''')

            conn.commit()

    @classmethod
    def _get_instance(cls):
        """Get singleton instance"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_repositories(cls, customer_id: str = "default") -> Dict[str, Any]:
        """
        Get all connected repositories for a customer

        Args:
            customer_id: Customer identifier

        Returns:
            Dict containing repositories list
        """
        try:
            instance = cls._get_instance()

            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT resource_id, resource_name, resource_data, provider_id, token_id, created_at
                    FROM customer_context
                    WHERE customer_id = ? AND resource_type = 'repository' AND is_active = 1
                    ORDER BY created_at DESC
                ''', (customer_id,))

                repositories = []
                for row in cursor.fetchall():
                    resource_data = json.loads(row[2])
                    repositories.append({
                        "id": row[0],
                        "name": row[1],
                        "url": resource_data.get("url"),
                        "branch": resource_data.get("branch", "main"),
                        "provider_id": row[3],
                        "token_id": row[4],
                        "created_at": row[5],
                        **resource_data
                    })

                return {
                    "status": "success",
                    "repositories": repositories,
                    "count": len(repositories),
                    "customer_id": customer_id,
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get repositories: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def add_repository(cls, repo_data: Dict[str, Any], customer_id: str = "default") -> Dict[str, Any]:
        """
        Add a new repository to customer context

        Args:
            repo_data: Repository configuration data
            customer_id: Customer identifier

        Returns:
            Dict containing operation result
        """
        try:
            instance = cls._get_instance()

            # Generate unique ID
            repo_id = str(uuid.uuid4())

            # Prepare resource data
            resource_data = {
                "name": repo_data["name"],
                "url": repo_data["url"],
                "branch": repo_data.get("branch", "main"),
                "access_token": repo_data.get("accessToken", ""),
                "type": repo_data.get("type", "git"),
                "status": "connected"
            }

            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO customer_context
                    (customer_id, resource_id, resource_type, resource_name, resource_data, provider_id, token_id)
                    VALUES (?, ?, 'repository', ?, ?, ?, ?)
                ''', (
                    customer_id,
                    repo_id,
                    repo_data["name"],
                    json.dumps(resource_data),
                    repo_data.get("provider_id", "manual"),
                    repo_data.get("token_id")
                ))
                conn.commit()

            # TODO: In production, trigger repository cloning and RAG indexing
            # This would involve:
            # 1. Clone the repository using git
            # 2. Extract code files and documentation
            # 3. Send to embedding service for RAG indexing
            # 4. Store document IDs for context retrieval

            return {
                "status": "success",
                "repository": {
                    "id": repo_id,
                    "customer_id": customer_id,
                    **resource_data
                },
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
    def get_mcp_resources(cls, customer_id: str = "default") -> Dict[str, Any]:
        """
        Get all MCP resources in context for a customer

        Args:
            customer_id: Customer identifier

        Returns:
            Dict containing MCP resources list
        """
        try:
            instance = cls._get_instance()

            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT resource_id, resource_type, resource_name, resource_data, provider_id, token_id, created_at
                    FROM customer_context
                    WHERE customer_id = ? AND resource_type != 'repository' AND is_active = 1
                    ORDER BY created_at DESC
                ''', (customer_id,))

                mcp_resources = []
                for row in cursor.fetchall():
                    resource_data = json.loads(row[3])
                    mcp_resources.append({
                        "resource_id": row[0],
                        "resource_type": row[1],
                        "resource_name": row[2],
                        "provider_id": row[4],
                        "token_id": row[5],
                        "created_at": row[6],
                        "resource_data": resource_data
                    })

                return {
                    "status": "success",
                    "resources": mcp_resources,
                    "count": len(mcp_resources),
                    "customer_id": customer_id,
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get MCP resources: {str(e)}",
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
