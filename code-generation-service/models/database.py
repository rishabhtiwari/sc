"""
Database models and initialization for code generation service
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for user context and repositories"""
    
    def __init__(self, db_path: str = "data/code_generation.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create repositories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repository_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        branch TEXT NOT NULL DEFAULT 'main',
                        provider TEXT NOT NULL DEFAULT 'github',
                        provider_id TEXT,
                        token_id TEXT,
                        status TEXT NOT NULL DEFAULT 'connecting',
                        local_path TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_context table for storing user-specific context
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_context (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL DEFAULT 'default',
                        repository_id TEXT NOT NULL,
                        context_type TEXT NOT NULL DEFAULT 'repository',
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (repository_id) REFERENCES repositories (repository_id),
                        UNIQUE(user_id, repository_id)
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_repositories_status ON repositories(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_context_user_id ON user_context(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_context_active ON user_context(is_active)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_repository(self, repository_data: Dict) -> str:
        """Add a new repository to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Generate repository ID if not provided
                repository_id = repository_data.get('repository_id') or f"repo_{int(datetime.now().timestamp())}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO repositories 
                    (repository_id, name, url, branch, provider, provider_id, token_id, status, local_path, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    repository_id,
                    repository_data.get('name', ''),
                    repository_data.get('url', ''),
                    repository_data.get('branch', 'main'),
                    repository_data.get('provider', 'github'),
                    repository_data.get('provider_id'),
                    repository_data.get('token_id'),
                    repository_data.get('status', 'connecting'),
                    repository_data.get('local_path'),
                    json.dumps(repository_data.get('metadata', {}))
                ))
                
                conn.commit()
                logger.info(f"Repository {repository_id} added to database")
                return repository_id
                
        except Exception as e:
            logger.error(f"Failed to add repository: {e}")
            raise
    
    def get_repositories(self, user_id: str = 'default') -> List[Dict]:
        """Get all repositories for a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT r.*, uc.is_active, uc.created_at as added_at
                    FROM repositories r
                    LEFT JOIN user_context uc ON r.repository_id = uc.repository_id AND uc.user_id = ?
                    WHERE uc.is_active = 1 OR uc.is_active IS NULL
                    ORDER BY r.created_at DESC
                ''', (user_id,))
                
                rows = cursor.fetchall()
                repositories = []
                
                for row in rows:
                    repo_data = {
                        'id': row['repository_id'],
                        'repository_id': row['repository_id'],
                        'name': row['name'],
                        'url': row['url'],
                        'branch': row['branch'],
                        'provider': row['provider'],
                        'provider_id': row['provider_id'],
                        'token_id': row['token_id'],
                        'status': row['status'],
                        'local_path': row['local_path'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'added_at': row['added_at']
                    }
                    repositories.append(repo_data)
                
                return repositories
                
        except Exception as e:
            logger.error(f"Failed to get repositories: {e}")
            raise
    
    def update_repository_status(self, repository_id: str, status: str, local_path: str = None):
        """Update repository status and local path"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if local_path:
                    cursor.execute('''
                        UPDATE repositories 
                        SET status = ?, local_path = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE repository_id = ?
                    ''', (status, local_path, repository_id))
                else:
                    cursor.execute('''
                        UPDATE repositories 
                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE repository_id = ?
                    ''', (status, repository_id))
                
                conn.commit()
                logger.info(f"Repository {repository_id} status updated to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update repository status: {e}")
            raise
    
    def add_to_user_context(self, user_id: str, repository_id: str):
        """Add repository to user context"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_context 
                    (user_id, repository_id, context_type, is_active)
                    VALUES (?, ?, 'repository', 1)
                ''', (user_id, repository_id))
                
                conn.commit()
                logger.info(f"Repository {repository_id} added to user {user_id} context")
                
        except Exception as e:
            logger.error(f"Failed to add repository to user context: {e}")
            raise
    
    def remove_from_user_context(self, user_id: str, repository_id: str):
        """Remove repository from user context"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_context 
                    SET is_active = 0
                    WHERE user_id = ? AND repository_id = ?
                ''', (user_id, repository_id))
                
                conn.commit()
                logger.info(f"Repository {repository_id} removed from user {user_id} context")
                
        except Exception as e:
            logger.error(f"Failed to remove repository from user context: {e}")
            raise

    def remove_repository(self, repository_id: str):
        """Remove repository from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Delete from repositories table
                cursor.execute('''
                    DELETE FROM repositories
                    WHERE repository_id = ?
                ''', (repository_id,))

                conn.commit()
                logger.info(f"Repository {repository_id} removed from database")

        except Exception as e:
            logger.error(f"Failed to remove repository from database: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()
