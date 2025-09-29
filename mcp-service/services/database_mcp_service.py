"""
Database MCP Service - Handles database connections and operations
"""

import logging
import time
import uuid
import json
from typing import Dict, List, Optional, Any
import psycopg2
import mysql.connector
import sqlite3
from contextlib import contextmanager

from config.settings import MCPConfig


class DatabaseMCPService:
    """Service for managing database MCP connections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = MCPConfig()
        self.connections: Dict[str, Dict[str, Any]] = {}
    
    def configure_provider(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure database provider with connection details
        
        Args:
            config_data: Database configuration data
            
        Returns:
            Dict with configuration result
        """
        try:
            # Validate required fields
            required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
            for field in required_fields:
                if field not in config_data:
                    return {
                        "status": "error",
                        "error": f"Missing required field: {field}"
                    }
            
            # Test database connection
            connection_test = self._test_connection(config_data)
            if connection_test['status'] != 'success':
                return connection_test
            
            # Store configuration
            config_id = str(uuid.uuid4())
            self.connections[config_id] = {
                **config_data,
                'config_id': config_id,
                'created_at': int(time.time() * 1000),
                'status': 'configured'
            }
            
            self.logger.info(f"✅ Database provider configured: {config_data['db_type']} - {config_data['database']}")
            
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Database provider configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Database configuration failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Configuration failed: {str(e)}"
            }
    
    def _test_connection(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection"""
        try:
            db_type = config_data['db_type']
            
            if db_type == 'postgresql':
                return self._test_postgresql_connection(config_data)
            elif db_type == 'mysql':
                return self._test_mysql_connection(config_data)
            elif db_type == 'sqlite':
                return self._test_sqlite_connection(config_data)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported database type: {db_type}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Connection test failed: {str(e)}"
            }
    
    def _test_postgresql_connection(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=config_data['host'],
                port=config_data['port'],
                database=config_data['database'],
                user=config_data['username'],
                password=config_data['password'],
                connect_timeout=10
            )
            conn.close()
            return {"status": "success", "message": "PostgreSQL connection successful"}
        except Exception as e:
            return {"status": "error", "error": f"PostgreSQL connection failed: {str(e)}"}
    
    def _test_mysql_connection(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test MySQL connection"""
        try:
            conn = mysql.connector.connect(
                host=config_data['host'],
                port=config_data['port'],
                database=config_data['database'],
                user=config_data['username'],
                password=config_data['password'],
                connection_timeout=10
            )
            conn.close()
            return {"status": "success", "message": "MySQL connection successful"}
        except Exception as e:
            return {"status": "error", "error": f"MySQL connection failed: {str(e)}"}
    
    def _test_sqlite_connection(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test SQLite connection"""
        try:
            conn = sqlite3.connect(config_data['database'], timeout=10)
            conn.close()
            return {"status": "success", "message": "SQLite connection successful"}
        except Exception as e:
            return {"status": "error", "error": f"SQLite connection failed: {str(e)}"}
    
    @contextmanager
    def get_connection(self, config_id: str):
        """Get database connection context manager"""
        if config_id not in self.connections:
            raise ValueError(f"Database configuration not found: {config_id}")
        
        config_data = self.connections[config_id]
        db_type = config_data['db_type']
        
        conn = None
        try:
            if db_type == 'postgresql':
                conn = psycopg2.connect(
                    host=config_data['host'],
                    port=config_data['port'],
                    database=config_data['database'],
                    user=config_data['username'],
                    password=config_data['password']
                )
            elif db_type == 'mysql':
                conn = mysql.connector.connect(
                    host=config_data['host'],
                    port=config_data['port'],
                    database=config_data['database'],
                    user=config_data['username'],
                    password=config_data['password']
                )
            elif db_type == 'sqlite':
                conn = sqlite3.connect(config_data['database'])
            
            yield conn
            
        finally:
            if conn:
                conn.close()
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute database tool
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Dict with execution result
        """
        try:
            if tool_name == "execute_query":
                return self._execute_query(arguments)
            elif tool_name == "list_tables":
                return self._list_tables(arguments)
            elif tool_name == "describe_table":
                return self._describe_table(arguments)
            elif tool_name == "get_table_data":
                return self._get_table_data(arguments)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Database tool execution failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}"
            }
    
    def _execute_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query"""
        config_id = arguments.get('config_id')
        query = arguments.get('query')
        
        if not config_id or not query:
            return {"status": "error", "error": "Missing config_id or query"}
        
        try:
            with self.get_connection(config_id) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    return {
                        "status": "success",
                        "results": results,
                        "columns": columns,
                        "row_count": len(results)
                    }
                else:
                    conn.commit()
                    return {
                        "status": "success",
                        "message": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                        "rows_affected": cursor.rowcount
                    }
                    
        except Exception as e:
            return {"status": "error", "error": f"Query execution failed: {str(e)}"}
    
    def _list_tables(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List database tables"""
        config_id = arguments.get('config_id')
        
        if not config_id:
            return {"status": "error", "error": "Missing config_id"}
        
        try:
            config_data = self.connections[config_id]
            db_type = config_data['db_type']
            
            if db_type == 'postgresql':
                query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            elif db_type == 'mysql':
                query = "SHOW TABLES"
            elif db_type == 'sqlite':
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            
            with self.get_connection(config_id) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                tables = [row[0] for row in cursor.fetchall()]
                
                return {
                    "status": "success",
                    "tables": tables,
                    "count": len(tables)
                }
                
        except Exception as e:
            return {"status": "error", "error": f"Failed to list tables: {str(e)}"}
    
    def _describe_table(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Describe table structure"""
        config_id = arguments.get('config_id')
        table_name = arguments.get('table_name')
        
        if not config_id or not table_name:
            return {"status": "error", "error": "Missing config_id or table_name"}
        
        try:
            config_data = self.connections[config_id]
            db_type = config_data['db_type']
            
            if db_type == 'postgresql':
                query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
                """
            elif db_type == 'mysql':
                query = f"DESCRIBE {table_name}"
            elif db_type == 'sqlite':
                query = f"PRAGMA table_info({table_name})"
            
            with self.get_connection(config_id) as conn:
                cursor = conn.cursor()
                if db_type == 'postgresql':
                    cursor.execute(query, (table_name,))
                else:
                    cursor.execute(query)
                
                columns = cursor.fetchall()
                column_info = [dict(zip([desc[0] for desc in cursor.description], row)) for row in columns]
                
                return {
                    "status": "success",
                    "table_name": table_name,
                    "columns": column_info,
                    "column_count": len(column_info)
                }
                
        except Exception as e:
            return {"status": "error", "error": f"Failed to describe table: {str(e)}"}
    
    def _get_table_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get table data with optional limit"""
        config_id = arguments.get('config_id')
        table_name = arguments.get('table_name')
        limit = arguments.get('limit', 100)
        
        if not config_id or not table_name:
            return {"status": "error", "error": "Missing config_id or table_name"}
        
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            
            with self.get_connection(config_id) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return {
                    "status": "success",
                    "table_name": table_name,
                    "columns": columns,
                    "data": results,
                    "row_count": len(results),
                    "limit": limit
                }
                
        except Exception as e:
            return {"status": "error", "error": f"Failed to get table data: {str(e)}"}
    
    def get_connection_status(self, config_id: str) -> Dict[str, Any]:
        """Get connection status"""
        if config_id not in self.connections:
            return {"status": "error", "error": "Configuration not found"}
        
        config_data = self.connections[config_id]
        test_result = self._test_connection(config_data)
        
        return {
            "status": "success",
            "config_id": config_id,
            "database_type": config_data['db_type'],
            "database_name": config_data['database'],
            "connection_status": test_result['status'],
            "connection_message": test_result.get('message', test_result.get('error', ''))
        }
