"""
Job Instance Service for tracking async sync job states
"""
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class JobInstanceService:
    def __init__(self, config: Config):
        self.config = config
        self.db_path = 'data/job_instances.db'
        self._init_database()

    def _init_database(self):
        """Initialize the job instances database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS job_instances (
                        id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        connection_id TEXT,
                        status TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        total_files INTEGER DEFAULT 0,
                        processed_files INTEGER DEFAULT 0,
                        error_message TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                ''')
                
                # Create index for faster lookups
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_job_instances_connection_id 
                    ON job_instances(connection_id)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_job_instances_status 
                    ON job_instances(status)
                ''')
                
                conn.commit()
                logger.info("Job instances database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize job instances database: {str(e)}")
            raise

    def create_job_instance(self, job_type: str, connection_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Create a new job instance and return its ID"""
        try:
            job_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO job_instances 
                    (id, job_type, connection_id, status, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    job_type,
                    connection_id,
                    'pending',
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
            
            logger.info(f"Created job instance {job_id} for {job_type}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job instance: {str(e)}")
            raise

    def update_job_status(self, job_id: str, status: str, progress: int = None, 
                         total_files: int = None, processed_files: int = None,
                         error_message: str = None, metadata: Dict[str, Any] = None):
        """Update job instance status and progress"""
        try:
            update_fields = ['status = ?', 'updated_at = ?']
            update_values = [status, datetime.utcnow().isoformat()]
            
            if progress is not None:
                update_fields.append('progress = ?')
                update_values.append(progress)
            
            if total_files is not None:
                update_fields.append('total_files = ?')
                update_values.append(total_files)
            
            if processed_files is not None:
                update_fields.append('processed_files = ?')
                update_values.append(processed_files)
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                update_values.append(error_message)
            
            if metadata is not None:
                update_fields.append('metadata = ?')
                update_values.append(json.dumps(metadata))
            
            # Set timestamps based on status
            if status == 'running' and not self._has_started(job_id):
                update_fields.append('started_at = ?')
                update_values.append(datetime.utcnow().isoformat())
            elif status in ['completed', 'failed', 'cancelled']:
                update_fields.append('completed_at = ?')
                update_values.append(datetime.utcnow().isoformat())
            
            update_values.append(job_id)  # For WHERE clause
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f'''
                    UPDATE job_instances 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', update_values)
                conn.commit()
            
            logger.info(f"Updated job {job_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            raise

    def get_job_instance(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job instance by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM job_instances WHERE id = ?
                ''', (job_id,))
                
                row = cursor.fetchone()
                if row:
                    job_data = dict(row)
                    if job_data['metadata']:
                        job_data['metadata'] = json.loads(job_data['metadata'])
                    return job_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job instance {job_id}: {str(e)}")
            return None

    def get_connection_jobs(self, connection_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job instances for a connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM job_instances
                    WHERE connection_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (connection_id, limit))

                jobs = []
                for row in cursor.fetchall():
                    job_data = dict(row)
                    if job_data['metadata']:
                        job_data['metadata'] = json.loads(job_data['metadata'])
                    jobs.append(job_data)

                return jobs

        except Exception as e:
            logger.error(f"Failed to get connection jobs: {str(e)}")
            return []

    def get_active_connection_jobs(self, connection_id: str) -> List[Dict[str, Any]]:
        """Get active (pending/running) job instances for a specific connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM job_instances
                    WHERE connection_id = ? AND status IN ('pending', 'running')
                    ORDER BY created_at DESC
                ''', (connection_id,))

                jobs = []
                for row in cursor.fetchall():
                    job_data = dict(row)
                    if job_data['metadata']:
                        job_data['metadata'] = json.loads(job_data['metadata'])
                    jobs.append(job_data)

                return jobs

        except Exception as e:
            logger.error(f"Failed to get active connection jobs: {str(e)}")
            return []

    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active (pending/running) job instances"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM job_instances 
                    WHERE status IN ('pending', 'running')
                    ORDER BY created_at DESC
                ''')
                
                jobs = []
                for row in cursor.fetchall():
                    job_data = dict(row)
                    if job_data['metadata']:
                        job_data['metadata'] = json.loads(job_data['metadata'])
                    jobs.append(job_data)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Failed to get active jobs: {str(e)}")
            return []

    def cleanup_stale_jobs(self, max_age_minutes: int = 30):
        """Mark stale jobs as failed (jobs that are pending/running but haven't been updated recently)"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE job_instances
                    SET status = 'failed',
                        error_message = 'Job marked as stale - no updates for over {} minutes',
                        completed_at = ?,
                        updated_at = ?
                    WHERE status IN ('pending', 'running')
                    AND updated_at < ?
                """.format(max_age_minutes), (
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    cutoff_time.isoformat()
                ))

                stale_count = cursor.rowcount
                conn.commit()

                logger.info(f"Marked {stale_count} stale jobs as failed")
                return stale_count

        except Exception as e:
            logger.error(f"Failed to cleanup stale jobs: {str(e)}")
            return 0

    def cleanup_old_jobs(self, days: int = 7):
        """Clean up job instances older than specified days"""
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM job_instances 
                    WHERE created_at < ? AND status IN ('completed', 'failed', 'cancelled')
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old job instances")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {str(e)}")

    def _has_started(self, job_id: str) -> bool:
        """Check if job has already been started"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT started_at FROM job_instances WHERE id = ?
                ''', (job_id,))
                
                row = cursor.fetchone()
                return row and row[0] is not None
                
        except Exception as e:
            logger.error(f"Failed to check job start status: {str(e)}")
            return False
