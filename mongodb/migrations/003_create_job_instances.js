// Migration: 003_create_job_instances.js
// Description: Create job_instances collection for tracking job execution across all job services
// Created: 2025-10-19

print('Starting migration: 003_create_job_instances');

// Switch to ichat_db database
use ichat_db;

// Create job_instances collection
db.createCollection('job_instances');

// Create indexes for the job_instances collection
db.getCollection('job_instances').createIndex({ "job_id": 1 }, { unique: true }); // Unique job ID
db.getCollection('job_instances').createIndex({ "job_type": 1 }); // Filter by job type
db.getCollection('job_instances').createIndex({ "status": 1 }); // Filter by status
db.getCollection('job_instances').createIndex({ "created_at": 1 }); // Sort by creation time
db.getCollection('job_instances').createIndex({ "job_type": 1, "status": 1 }); // Compound index for filtering
db.getCollection('job_instances').createIndex({ "job_type": 1, "created_at": -1 }); // Recent jobs by type

print('✓ Created job_instances collection with indexes');

// Schema structure for job_instances collection:
// {
//     "job_id": "string (unique identifier for the job instance)",
//     "job_type": "string (type of job: news_fetch, github_sync, remote_host_sync, etc.)",
//     "status": "string (pending, running, completed, failed)",
//     "created_at": "Date (when job instance was created)",
//     "updated_at": "Date (when job instance was last updated)",
//     "started_at": "Date (when job execution started, null if not started)",
//     "completed_at": "Date (when job execution completed, null if not completed)",
//     "error_message": "string (error message if job failed, null if successful)",
//     "result": "object (job execution results and statistics)",
//     "metadata": "object (additional job metadata like trigger type, parameters, etc.)",
//     "progress": "number (current progress count, default 0)",
//     "total_items": "number (total items to process, default 0)"
// }

print('✓ Job instances collection created for common job framework');
print('Migration 003_create_job_instances completed successfully');
