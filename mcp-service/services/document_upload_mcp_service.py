"""
Document Upload MCP Service - Handles document uploads and processing for RAG
"""

import logging
import time
import uuid
import os
import shutil
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

from config.settings import MCPConfig


class DocumentUploadMCPService:
    """Service for managing document upload MCP operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = MCPConfig()
        self.configurations: Dict[str, Dict[str, Any]] = {}
    
    def configure_provider(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure document upload provider
        
        Args:
            config_data: Document upload configuration data
            
        Returns:
            Dict with configuration result
        """
        try:
            # Validate required fields
            required_fields = ['storage_path', 'max_file_size', 'allowed_extensions']
            for field in required_fields:
                if field not in config_data:
                    return {
                        "status": "error",
                        "error": f"Missing required field: {field}"
                    }
            
            # Validate storage path
            storage_path = Path(config_data['storage_path'])
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
                if not storage_path.is_dir():
                    return {
                        "status": "error",
                        "error": f"Storage path is not a directory: {storage_path}"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Cannot create storage directory: {str(e)}"
                }
            
            # Validate file size
            try:
                max_file_size = int(config_data['max_file_size'])
                if max_file_size <= 0:
                    return {
                        "status": "error",
                        "error": "Max file size must be a positive number"
                    }
            except ValueError:
                return {
                    "status": "error",
                    "error": "Max file size must be a valid number"
                }
            
            # Validate extensions
            allowed_extensions = [ext.strip().lower() for ext in config_data['allowed_extensions'].split(',')]
            if not allowed_extensions:
                return {
                    "status": "error",
                    "error": "At least one file extension must be allowed"
                }
            
            # Store configuration
            config_id = str(uuid.uuid4())
            self.configurations[config_id] = {
                **config_data,
                'config_id': config_id,
                'allowed_extensions': allowed_extensions,
                'max_file_size_bytes': max_file_size * 1024 * 1024,  # Convert MB to bytes
                'created_at': int(time.time() * 1000),
                'status': 'configured'
            }
            
            self.logger.info(f"✅ Document upload provider configured: {storage_path}")
            
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Document upload provider configured successfully",
                "storage_path": str(storage_path),
                "max_file_size_mb": max_file_size,
                "allowed_extensions": allowed_extensions
            }
            
        except Exception as e:
            self.logger.error(f"❌ Document upload configuration failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Configuration failed: {str(e)}"
            }
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute document upload tool
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Dict with execution result
        """
        try:
            if tool_name == "upload_document":
                return self._upload_document(arguments)
            elif tool_name == "list_documents":
                return self._list_documents(arguments)
            elif tool_name == "delete_document":
                return self._delete_document(arguments)
            elif tool_name == "get_document_info":
                return self._get_document_info(arguments)
            elif tool_name == "process_document":
                return self._process_document(arguments)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Document upload tool execution failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}"
            }
    
    def _upload_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a document"""
        config_id = arguments.get('config_id')
        file_path = arguments.get('file_path')
        file_name = arguments.get('file_name')
        
        if not config_id or not file_path:
            return {"status": "error", "error": "Missing config_id or file_path"}
        
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        
        try:
            # Validate file exists
            source_path = Path(file_path)
            if not source_path.exists():
                return {"status": "error", "error": f"File not found: {file_path}"}
            
            # Validate file size
            file_size = source_path.stat().st_size
            if file_size > config['max_file_size_bytes']:
                return {
                    "status": "error", 
                    "error": f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({config['max_file_size']}MB)"
                }
            
            # Validate file extension
            file_extension = source_path.suffix.lower().lstrip('.')
            if file_extension not in config['allowed_extensions']:
                return {
                    "status": "error",
                    "error": f"File extension '{file_extension}' not allowed. Allowed: {', '.join(config['allowed_extensions'])}"
                }
            
            # Generate unique filename if not provided
            if not file_name:
                file_name = source_path.name
            
            # Ensure unique filename
            storage_path = Path(config['storage_path'])
            dest_path = storage_path / file_name
            counter = 1
            while dest_path.exists():
                name_parts = file_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_name = f"{file_name}_{counter}"
                dest_path = storage_path / new_name
                counter += 1
            
            # Copy file to storage
            shutil.copy2(source_path, dest_path)
            
            # Get file info
            file_info = {
                "file_id": str(uuid.uuid4()),
                "original_name": file_name,
                "stored_name": dest_path.name,
                "file_path": str(dest_path),
                "file_size": file_size,
                "file_extension": file_extension,
                "mime_type": mimetypes.guess_type(str(dest_path))[0],
                "uploaded_at": int(time.time() * 1000)
            }
            
            # Auto-process if enabled
            if config.get('auto_process', 'true').lower() == 'true':
                process_result = self._process_document_for_rag(dest_path, file_info)
                file_info['processing_result'] = process_result
            
            self.logger.info(f"✅ Document uploaded: {dest_path.name}")
            
            return {
                "status": "success",
                "message": "Document uploaded successfully",
                "file_info": file_info
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Upload failed: {str(e)}"}
    
    def _list_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List uploaded documents"""
        config_id = arguments.get('config_id')
        
        if not config_id:
            return {"status": "error", "error": "Missing config_id"}
        
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        
        try:
            storage_path = Path(config['storage_path'])
            documents = []
            
            for file_path in storage_path.iterdir():
                if file_path.is_file():
                    file_stat = file_path.stat()
                    documents.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_stat.st_size,
                        "extension": file_path.suffix.lower().lstrip('.'),
                        "mime_type": mimetypes.guess_type(str(file_path))[0],
                        "modified_at": int(file_stat.st_mtime * 1000)
                    })
            
            # Sort by modification time (newest first)
            documents.sort(key=lambda x: x['modified_at'], reverse=True)
            
            return {
                "status": "success",
                "documents": documents,
                "count": len(documents),
                "storage_path": str(storage_path)
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Failed to list documents: {str(e)}"}
    
    def _delete_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a document"""
        config_id = arguments.get('config_id')
        file_name = arguments.get('file_name')
        
        if not config_id or not file_name:
            return {"status": "error", "error": "Missing config_id or file_name"}
        
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        
        try:
            storage_path = Path(config['storage_path'])
            file_path = storage_path / file_name
            
            if not file_path.exists():
                return {"status": "error", "error": f"File not found: {file_name}"}
            
            file_path.unlink()
            
            self.logger.info(f"✅ Document deleted: {file_name}")
            
            return {
                "status": "success",
                "message": f"Document '{file_name}' deleted successfully"
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Delete failed: {str(e)}"}
    
    def _get_document_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get document information"""
        config_id = arguments.get('config_id')
        file_name = arguments.get('file_name')
        
        if not config_id or not file_name:
            return {"status": "error", "error": "Missing config_id or file_name"}
        
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        
        try:
            storage_path = Path(config['storage_path'])
            file_path = storage_path / file_name
            
            if not file_path.exists():
                return {"status": "error", "error": f"File not found: {file_name}"}
            
            file_stat = file_path.stat()
            
            return {
                "status": "success",
                "file_info": {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "extension": file_path.suffix.lower().lstrip('.'),
                    "mime_type": mimetypes.guess_type(str(file_path))[0],
                    "created_at": int(file_stat.st_ctime * 1000),
                    "modified_at": int(file_stat.st_mtime * 1000),
                    "accessed_at": int(file_stat.st_atime * 1000)
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Failed to get document info: {str(e)}"}
    
    def _process_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Process document for RAG integration"""
        config_id = arguments.get('config_id')
        file_name = arguments.get('file_name')
        
        if not config_id or not file_name:
            return {"status": "error", "error": "Missing config_id or file_name"}
        
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        
        try:
            storage_path = Path(config['storage_path'])
            file_path = storage_path / file_name
            
            if not file_path.exists():
                return {"status": "error", "error": f"File not found: {file_name}"}
            
            # Process document for RAG
            result = self._process_document_for_rag(file_path, {"name": file_name})
            
            return {
                "status": "success",
                "message": f"Document '{file_name}' processed successfully",
                "processing_result": result
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Processing failed: {str(e)}"}
    
    def _process_document_for_rag(self, file_path: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process document for RAG integration"""
        try:
            # This would integrate with the embedding service
            # For now, return a placeholder result
            
            self.logger.info(f"🔄 Processing document for RAG: {file_path.name}")
            
            # TODO: Integrate with embedding service
            # - Extract text from document
            # - Split into chunks
            # - Generate embeddings
            # - Store in vector database
            
            return {
                "status": "success",
                "message": "Document processed for RAG (placeholder implementation)",
                "chunks_created": 0,
                "embeddings_generated": 0,
                "processing_time": 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ RAG processing failed: {str(e)}")
            return {
                "status": "error",
                "error": f"RAG processing failed: {str(e)}"
            }
    
    def get_configuration_status(self, config_id: str) -> Dict[str, Any]:
        """Get configuration status"""
        if config_id not in self.configurations:
            return {"status": "error", "error": "Configuration not found"}
        
        config = self.configurations[config_id]
        storage_path = Path(config['storage_path'])
        
        # Count documents
        document_count = 0
        total_size = 0
        
        try:
            for file_path in storage_path.iterdir():
                if file_path.is_file():
                    document_count += 1
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        
        return {
            "status": "success",
            "config_id": config_id,
            "storage_path": str(storage_path),
            "storage_exists": storage_path.exists(),
            "document_count": document_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "max_file_size_mb": config['max_file_size'],
            "allowed_extensions": config['allowed_extensions'],
            "auto_process": config.get('auto_process', 'true')
        }
