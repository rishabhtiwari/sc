// Migration: 025_add_customer_id_to_job_instances.js
// Description: Add customer_id field to job_instances collection for multi-tenant job support
// Created: 2025-12-16

print('Starting migration: 025_add_customer_id_to_job_instances');

// Switch to news database (where job_instances are stored)
use news;

// Add customer_id field to existing job_instances (set to null for existing jobs)
db.job_instances.updateMany(
    { customer_id: { $exists: false } },
    { $set: { customer_id: null } }
);

print('✓ Added customer_id field to existing job_instances');

// Drop old indexes
try {
    db.job_instances.dropIndex('job_type_1_status_1');
    print('✓ Dropped old compound index: job_type_1_status_1');
} catch (e) {
    print('⚠ Index job_type_1_status_1 does not exist, skipping');
}

try {
    db.job_instances.dropIndex('job_type_1_created_at_-1');
    print('✓ Dropped old compound index: job_type_1_created_at_-1');
} catch (e) {
    print('⚠ Index job_type_1_created_at_-1 does not exist, skipping');
}

// Create new compound indexes with customer_id
db.job_instances.createIndex(
    { customer_id: 1, job_type: 1, status: 1 },
    { name: 'customer_job_type_status_idx' }
);
print('✓ Created compound index: customer_id + job_type + status');

db.job_instances.createIndex(
    { customer_id: 1, job_type: 1, created_at: -1 },
    { name: 'customer_job_type_created_idx' }
);
print('✓ Created compound index: customer_id + job_type + created_at');

// Keep single-field indexes for backward compatibility
db.job_instances.createIndex({ job_type: 1 });
print('✓ Created index: job_type');

db.job_instances.createIndex({ status: 1 });
print('✓ Created index: status');

print('✅ Migration 025_add_customer_id_to_job_instances completed successfully');

// Updated schema structure for job_instances collection:
// {
//     "job_id": "string (unique identifier for the job instance)",
//     "customer_id": "string (customer ID for multi-tenant support, null for system jobs)",
//     "job_type": "string (type of job: news_fetch, github_sync, remote_host_sync, etc.)",
//     "status": "string (pending, running, completed, failed, cancelled)",
//     "created_at": "Date (when job instance was created)",
//     "updated_at": "Date (when job instance was last updated)",
//     "started_at": "Date (when job execution started, null if not started)",
//     "completed_at": "Date (when job execution completed, null if not completed)",
//     "error_message": "string (error message if job failed, null if successful)",
//     "result": "object (job execution results and statistics)",
//     "metadata": "object (additional job metadata)",
//     "progress": "number (job progress percentage 0-100)",
//     "total_items": "number (total items to process)",
//     "cancelled": "boolean (whether job was cancelled)"
// }

