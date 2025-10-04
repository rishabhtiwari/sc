"""
Job Instance Service for GitHub Repository Syncer
Manages job instances and their lifecycle
"""
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class JobInstanceService:
    """Service for managing job instances"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.JOB_INSTANCES_DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Initialize job instances database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_instances (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    repository_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    total_files INTEGER DEFAULT 0,
                    processed_files INTEGER DEFAULT 0,
                    metadata TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_status ON job_instances(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_repository ON job_instances(repository_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_created ON job_instances(created_at)')
            
            conn.commit()
    
    def create_job_instance(self, job_type: str, repository_id: str = None, 
                          metadata: Dict[str, Any] = None) -> str:
        """Create a new job instance"""
        job_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO job_instances 
                (id, job_type, repository_id, metadata, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (job_id, job_type, repository_id, metadata_json))
            conn.commit()
        
        return job_id
    
    def get_job_instance(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job instance by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, job_type, repository_id, status, progress, total_files, 
                       processed_files, metadata, error_message, created_at, 
                       updated_at, started_at, completed_at
                FROM job_instances WHERE id = ?
            ''', (job_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'job_type': row[1],
                'repository_id': row[2],
                'status': row[3],
                'progress': row[4],
                'total_files': row[5],
                'processed_files': row[6],
                'metadata': json.loads(row[7]) if row[7] else {},
                'error_message': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'started_at': row[11],
                'completed_at': row[12]
            }
    
    def update_job_status(self, job_id: str, status: str, error_message: str = None):
        """Update job status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Set timestamps based on status
            if status == 'running':
                cursor.execute('''
                    UPDATE job_instances 
                    SET status = ?, error_message = ?, started_at = CURRENT_TIMESTAMP, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, error_message, job_id))
            elif status in ['completed', 'failed', 'cancelled']:
                cursor.execute('''
                    UPDATE job_instances 
                    SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, error_message, job_id))
            else:
                cursor.execute('''
                    UPDATE job_instances 
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, error_message, job_id))
            
            conn.commit()
    
    def update_job_progress(self, job_id: str, progress: int, total_files: int = None, 
                          processed_files: int = None):
        """Update job progress"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            update_parts = ['progress = ?', 'updated_at = CURRENT_TIMESTAMP']
            params = [progress]
            
            if total_files is not None:
                update_parts.append('total_files = ?')
                params.append(total_files)
            
            if processed_files is not None:
                update_parts.append('processed_files = ?')
                params.append(processed_files)
            
            params.append(job_id)
            
            query = f'''
                UPDATE job_instances 
                SET {', '.join(update_parts)}
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            conn.commit()
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active (pending/running) jobs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, job_type, repository_id, status, progress, total_files, 
                       processed_files, metadata, error_message, created_at, 
                       updated_at, started_at, completed_at
                FROM job_instances 
                WHERE status IN ('pending', 'running')
                ORDER BY created_at ASC
            ''')
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    'id': row[0],
                    'job_type': row[1],
                    'repository_id': row[2],
                    'status': row[3],
                    'progress': row[4],
                    'total_files': row[5],
                    'processed_files': row[6],
                    'metadata': json.loads(row[7]) if row[7] else {},
                    'error_message': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'started_at': row[11],
                    'completed_at': row[12]
                })
            
            return jobs
    
    def get_active_repository_jobs(self, repository_id: str) -> List[Dict[str, Any]]:
        """Get active jobs for a specific repository"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, job_type, repository_id, status, progress, total_files, 
                       processed_files, metadata, error_message, created_at, 
                       updated_at, started_at, completed_at
                FROM job_instances 
                WHERE repository_id = ? AND status IN ('pending', 'running')
                ORDER BY created_at ASC
            ''', (repository_id,))
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    'id': row[0],
                    'job_type': row[1],
                    'repository_id': row[2],
                    'status': row[3],
                    'progress': row[4],
                    'total_files': row[5],
                    'processed_files': row[6],
                    'metadata': json.loads(row[7]) if row[7] else {},
                    'error_message': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'started_at': row[11],
                    'completed_at': row[12]
                })
            
            return jobs
    
    def get_repository_jobs(self, repository_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent jobs for a repository"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, job_type, repository_id, status, progress, total_files, 
                       processed_files, metadata, error_message, created_at, 
                       updated_at, started_at, completed_at
                FROM job_instances 
                WHERE repository_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (repository_id, limit))
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    'id': row[0],
                    'job_type': row[1],
                    'repository_id': row[2],
                    'status': row[3],
                    'progress': row[4],
                    'total_files': row[5],
                    'processed_files': row[6],
                    'metadata': json.loads(row[7]) if row[7] else {},
                    'error_message': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'started_at': row[11],
                    'completed_at': row[12]
                })
            
            return jobs
    
    def cleanup_stale_jobs(self, max_age_minutes: int = 30) -> int:
        """Mark stale jobs as failed"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE job_instances 
                SET status = 'failed', 
                    error_message = 'Job marked as stale (exceeded max age)',
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE status IN ('pending', 'running') 
                AND updated_at < ?
            ''', (cutoff_time.isoformat(),))
            
            stale_count = cursor.rowcount
            conn.commit()
            
            return stale_count
    
    def delete_old_jobs(self, days_old: int = 30) -> int:
        """Delete old completed jobs"""
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM job_instances 
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND completed_at < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
