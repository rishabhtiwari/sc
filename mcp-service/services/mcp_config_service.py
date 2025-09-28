"""
MCP Configuration Service - Handles MCP configuration storage and retrieval
"""

import json
import uuid
import time
import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from config.settings import MCPConfig


class MCPConfigService:
    """Service for managing MCP configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = MCPConfig()
        self.storage_path = Path(self.config.MCP_CONFIG_STORAGE_PATH)
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for configurations
        self.configs_cache: Dict[str, Dict[str, Any]] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load configurations from storage"""
        try:
            config_files = list(self.storage_path.glob("*.json"))
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                        config_id = config_file.stem
                        self.configs_cache[config_id] = config_data
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to load config {config_file}: {str(e)}")
            
            self.logger.info(f"📁 Loaded {len(self.configs_cache)} MCP configurations")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load configurations: {str(e)}")
    
    def store_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store an MCP configuration
        
        Args:
            config_data: Configuration data to store
            
        Returns:
            Dict with storage result
        """
        try:
            # Generate unique config ID
            config_id = str(uuid.uuid4())
            
            # Add metadata
            config_with_metadata = {
                **config_data,
                "config_id": config_id,
                "created_at": int(time.time() * 1000),
                "updated_at": int(time.time() * 1000)
            }
            
            # Save to file
            config_file = self.storage_path / f"{config_id}.json"
            with open(config_file, 'w') as f:
                json.dump(config_with_metadata, f, indent=2)
            
            # Update cache
            self.configs_cache[config_id] = config_with_metadata
            
            self.logger.info(f"✅ Successfully stored MCP config: {config_data.get('name', 'unnamed')}")
            
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Configuration stored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to store configuration: {str(e)}"
            }
    
    def get_config(self, config_id: str) -> Dict[str, Any]:
        """
        Get an MCP configuration
        
        Args:
            config_id: Configuration ID to retrieve
            
        Returns:
            Dict with configuration data or error
        """
        try:
            if config_id in self.configs_cache:
                return {
                    "status": "success",
                    "config": self.configs_cache[config_id]
                }
            else:
                return {
                    "status": "error",
                    "error": "Configuration not found"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to retrieve configuration: {str(e)}"
            }
    
    def delete_config(self, config_id: str) -> Dict[str, Any]:
        """
        Delete an MCP configuration
        
        Args:
            config_id: Configuration ID to delete
            
        Returns:
            Dict with deletion result
        """
        try:
            if config_id not in self.configs_cache:
                return {
                    "status": "error",
                    "error": "Configuration not found"
                }
            
            # Remove from file system
            config_file = self.storage_path / f"{config_id}.json"
            if config_file.exists():
                config_file.unlink()
            
            # Remove from cache
            config_name = self.configs_cache[config_id].get('name', 'unnamed')
            del self.configs_cache[config_id]
            
            self.logger.info(f"✅ Successfully deleted MCP config: {config_name}")
            
            return {
                "status": "success",
                "message": "Configuration deleted successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to delete configuration: {str(e)}"
            }
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """
        List all stored configurations
        
        Returns:
            List of configuration summaries
        """
        try:
            configs_list = []
            
            for config_id, config_data in self.configs_cache.items():
                # Create summary without sensitive data
                config_summary = {
                    "config_id": config_id,
                    "name": config_data.get('name', 'unnamed'),
                    "description": config_data.get('description', ''),
                    "protocol": config_data.get('protocol', 'stdio'),
                    "created_at": config_data.get('created_at'),
                    "updated_at": config_data.get('updated_at'),
                    "command": config_data.get('command', [])
                }
                configs_list.append(config_summary)
            
            # Sort by creation time (newest first)
            configs_list.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            
            return configs_list
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list configs: {str(e)}")
            return []
    
    def update_config(self, config_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing MCP configuration
        
        Args:
            config_id: Configuration ID to update
            config_data: New configuration data
            
        Returns:
            Dict with update result
        """
        try:
            if config_id not in self.configs_cache:
                return {
                    "status": "error",
                    "error": "Configuration not found"
                }
            
            # Merge with existing config
            existing_config = self.configs_cache[config_id]
            updated_config = {
                **existing_config,
                **config_data,
                "config_id": config_id,  # Preserve original ID
                "created_at": existing_config.get('created_at'),  # Preserve creation time
                "updated_at": int(time.time() * 1000)  # Update modification time
            }
            
            # Save to file
            config_file = self.storage_path / f"{config_id}.json"
            with open(config_file, 'w') as f:
                json.dump(updated_config, f, indent=2)
            
            # Update cache
            self.configs_cache[config_id] = updated_config
            
            self.logger.info(f"✅ Successfully updated MCP config: {updated_config.get('name', 'unnamed')}")
            
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Configuration updated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to update configuration: {str(e)}"
            }
