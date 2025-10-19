# MongoDB Database Service for iChat

This directory contains the MongoDB database service configuration for the iChat system with an integrated migration system.

## Overview

The MongoDB service provides persistent data storage for the iChat application, including:
- User management and authentication
- Chat conversations and messages
- Document metadata and tracking
- MCP (Model Context Protocol) connections
- Context resources and session management
- Async job tracking and status
- Repository synchronization status
- System configuration

## Migration System

This MongoDB setup includes a robust migration system that:
- ✅ Tracks executed migrations to prevent re-running
- ✅ Runs migrations in order during container startup
- ✅ Provides easy migration creation tools
- ✅ Supports rollback tracking and error handling
- ✅ Maintains migration history

## Service Configuration

### Container Details
- **Container Name**: `ichat-mongodb`
- **Build**: Custom Dockerfile with migration system
- **Port**: `27017` (mapped to host port 27017)
- **Network**: `ichat-network`

### Authentication
- **Root User**: `ichat_admin`
- **Root Password**: `ichat_secure_password_2024`
- **Application User**: `ichat_app`
- **Application Password**: `ichat_app_password_2024`
- **Database**: `ichat_db`

### Volumes
- `mongodb-data:/data/db` - Database files
- `mongodb-config:/data/configdb` - Configuration files
- `./mongodb/logs:/var/log/mongodb` - Log files

## Migration System Usage

### Creating New Migrations

Use the migration creation script to generate new migrations:

```bash
# Create a new migration
./mongodb/scripts/create-migration.sh "add_user_preferences_table"

# This creates: mongodb/migrations/003_add_user_preferences_table.js
```

### Migration File Structure

Migrations are JavaScript files that run in MongoDB shell context:

```javascript
// Migration: 003_add_user_preferences_table.js
// Description: add_user_preferences_table
// Date: 2024-01-01

print('Running migration: 003_add_user_preferences_table.js');

// Create new collection
db.createCollection('user_preferences');
db.user_preferences.createIndex({ "user_id": 1 }, { unique: true });

// Add new field to existing collection
db.users.updateMany({}, { $set: { preferences_id: null } });

print('Migration 003_add_user_preferences_table.js completed successfully');
```

### Migration Execution

Migrations run automatically when the container starts:
1. Container builds with all migration files
2. On startup, the migration system checks `_migrations` collection
3. Executes any migrations not yet run
4. Marks completed migrations to prevent re-execution

### Viewing Migration Status

```bash
# Connect to MongoDB and check migration history
docker exec -it ichat-mongodb mongosh -u ichat_app -p ichat_app_password_2024 ichat_db

# In MongoDB shell:
db._migrations.find().sort({executed_at: 1});
```

## Database Schema

### Collections

1. **users** - User accounts and profiles
   - Indexes: email (unique), username (unique), created_at

2. **sessions** - User session management
   - Indexes: session_id (unique), user_id, expires_at (TTL)

3. **conversations** - Chat conversation metadata
   - Indexes: user_id, created_at, updated_at

4. **messages** - Individual chat messages
   - Indexes: conversation_id, user_id, timestamp, message_type

5. **documents** - Uploaded document metadata
   - Indexes: user_id, document_id (unique), upload_date, document_type, status

6. **mcp_connections** - MCP provider connections
   - Indexes: user_id, provider_type, connection_id (unique), created_at

7. **context_resources** - Context management resources
   - Indexes: user_id, resource_type, resource_id, session_id

8. **job_instances** - Async job tracking
   - Indexes: job_id (unique), user_id, job_type, status, created_at, updated_at

9. **repository_sync_status** - Repository synchronization tracking
   - Indexes: repository_id (unique), user_id, last_sync_at, sync_status

10. **system_config** - System-wide configuration
    - Indexes: config_key (unique)

## Connection Strings

### From Application Services
```
mongodb://ichat_app:ichat_app_password_2024@ichat-mongodb:27017/ichat_db
```

### From Host (for development/debugging)
```
mongodb://ichat_admin:ichat_secure_password_2024@localhost:27017/ichat_db?authSource=admin
```

## Management Commands

### Connect to MongoDB Shell
```bash
# From host
docker exec -it ichat-mongodb mongosh -u ichat_admin -p ichat_secure_password_2024 --authenticationDatabase admin

# From within container
docker exec -it ichat-mongodb mongosh
```

### Backup Database
```bash
docker exec ichat-mongodb mongodump --username ichat_admin --password ichat_secure_password_2024 --authenticationDatabase admin --db ichat_db --out /data/backup
```

### Restore Database
```bash
docker exec ichat-mongodb mongorestore --username ichat_admin --password ichat_secure_password_2024 --authenticationDatabase admin --db ichat_db /data/backup/ichat_db
```

## Health Check

The service includes a health check that pings the MongoDB server every 30 seconds:
```bash
mongosh --eval "db.adminCommand('ping')"
```

## Resource Limits

- **Memory Limit**: 2GB
- **Memory Reservation**: 512MB

## Security Notes

1. **Change Default Passwords**: Update the passwords in docker-compose.yml for production use
2. **Network Security**: The service is only accessible within the ichat-network
3. **Authentication**: MongoDB runs with authentication enabled
4. **Logging**: All operations are logged to `/var/log/mongodb/mongod.log`

## Initialization

The database is automatically initialized with:
- Application user creation
- Collection creation with appropriate indexes
- Initial system configuration
- Proper security settings

The initialization script is located at `./mongodb/init/01-init-ichat-db.js` and runs only on the first container startup.

## Troubleshooting

### Check Service Status
```bash
docker-compose ps ichat-mongodb
```

### View Logs
```bash
docker-compose logs ichat-mongodb
```

### Check Database Connection
```bash
docker exec ichat-mongodb mongosh --eval "db.runCommand({connectionStatus: 1})"
```

### Monitor Performance
```bash
docker exec ichat-mongodb mongosh --eval "db.runCommand({serverStatus: 1})"
```
