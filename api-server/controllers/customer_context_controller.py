"""
Customer Context Controller - Business logic for customer-persistent context management
"""

import time
import uuid
import json
import os
import sqlite3
from typing import Dict, Any, List
from datetime import datetime


class CustomerContextController:
    """Controller for customer-persistent context management operations"""
    
    def __init__(self):
        self.db_path = "data/customer_context.db"
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
    def get_all_context_resources(cls, customer_id: str = "default") -> Dict[str, Any]:
        """
        Get all context resources for a customer (repositories, remote hosts, documents)
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Dict containing all context resources grouped by type
        """
        try:
            instance = cls._get_instance()
            
            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT resource_id, resource_type, resource_name, resource_data, provider_id, token_id, created_at
                    FROM customer_context 
                    WHERE customer_id = ? AND is_active = 1
                    ORDER BY resource_type, created_at DESC
                ''', (customer_id,))
                
                # Group resources by type
                resources_by_type = {
                    "repositories": [],
                    "remote_hosts": [],
                    "documents": []
                }
                
                for row in cursor.fetchall():
                    resource_data = json.loads(row[3])
                    resource = {
                        "id": row[0],
                        "provider_id": row[4],
                        "token_id": row[5],
                        "created_at": row[6],
                        **resource_data,
                        "name": row[2]  # Ensure database resource_name takes precedence
                    }
                    
                    resource_type = row[1]
                    if resource_type == "repository":
                        resources_by_type["repositories"].append(resource)
                    elif resource_type == "remote_host":
                        resources_by_type["remote_hosts"].append(resource)
                    elif resource_type == "document":
                        resources_by_type["documents"].append(resource)
                
                return {
                    "status": "success",
                    "customer_id": customer_id,
                    "resources": resources_by_type,
                    "total_count": sum(len(resources) for resources in resources_by_type.values()),
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get context resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def add_github_repository(cls, repo_data: Dict[str, Any], customer_id: str = "default") -> Dict[str, Any]:
        """
        Add GitHub repository to customer context
        
        Args:
            repo_data: Repository data from GitHub MCP
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
                "name": repo_data.get("name") or repo_data.get("full_name", "Unknown Repository"),
                "url": repo_data.get("clone_url"),
                "html_url": repo_data.get("html_url"),
                "branch": repo_data.get("default_branch", "main"),
                "description": repo_data.get("description", ""),
                "language": repo_data.get("language"),
                "stars": repo_data.get("stars", 0),
                "private": repo_data.get("private", False),
                "type": "git",
                "status": "connected"
            }
            
            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO customer_context 
                    (customer_id, resource_id, resource_type, resource_name, resource_data, provider_id, token_id)
                    VALUES (?, ?, 'repository', ?, ?, 'github', ?)
                ''', (
                    customer_id,
                    repo_id,
                    resource_data["name"],
                    json.dumps(resource_data),
                    repo_data.get("token_id")
                ))
                conn.commit()
            
            return {
                "status": "success",
                "repository": {
                    "id": repo_id,
                    "customer_id": customer_id,
                    **resource_data
                },
                "message": f"GitHub repository '{resource_data['name']}' added to context",
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to add GitHub repository: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def add_remote_host(cls, host_data: Dict[str, Any], customer_id: str = "default") -> Dict[str, Any]:
        """
        Add remote host to customer context
        
        Args:
            host_data: Remote host data from remote host MCP
            customer_id: Customer identifier
            
        Returns:
            Dict containing operation result
        """
        try:
            instance = cls._get_instance()
            
            # Generate unique ID
            host_id = str(uuid.uuid4())
            
            # Prepare resource data
            resource_data = {
                "name": host_data.get("name", "Unknown Host"),
                "protocol": host_data.get("protocol"),
                "host": host_data.get("host"),
                "port": host_data.get("port"),
                "username": host_data.get("username"),
                "base_path": host_data.get("base_path", "/"),
                "connection_id": host_data.get("connection_id"),
                "status": "connected"
            }
            
            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO customer_context 
                    (customer_id, resource_id, resource_type, resource_name, resource_data, provider_id, token_id)
                    VALUES (?, ?, 'remote_host', ?, ?, 'remote_host', ?)
                ''', (
                    customer_id,
                    host_id,
                    resource_data["name"],
                    json.dumps(resource_data),
                    host_data.get("token_id")
                ))
                conn.commit()
            
            return {
                "status": "success",
                "remote_host": {
                    "id": host_id,
                    "customer_id": customer_id,
                    **resource_data
                },
                "message": f"Remote host '{resource_data['name']}' added to context",
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to add remote host: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @classmethod
    def remove_context_resource(cls, resource_id: str, customer_id: str = "default") -> Dict[str, Any]:
        """
        Remove resource from customer context
        
        Args:
            resource_id: Resource ID to remove
            customer_id: Customer identifier
            
        Returns:
            Dict containing operation result
        """
        try:
            instance = cls._get_instance()
            
            with sqlite3.connect(instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE customer_context 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ? AND resource_id = ?
                ''', (customer_id, resource_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return {
                        "status": "success",
                        "message": "Resource removed from context",
                        "resource_id": resource_id,
                        "timestamp": int(time.time() * 1000)
                    }
                else:
                    return {
                        "status": "error",
                        "error": "Resource not found in context",
                        "resource_id": resource_id,
                        "timestamp": int(time.time() * 1000)
                    }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to remove resource: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
