# Remote Host Syncer Job

This job periodically syncs data from connected MCP remote host servers and refreshes indexing in the embedding service.

## Features

- **Scheduled Sync**: Runs on configurable frequency (daily, hourly, weekly)
- **Manual Trigger**: Supports on-demand sync via API endpoint
- **Connection-Specific Sync**: Sync individual connections on demand
- **Multi-Protocol Support**: SSH, SFTP, FTP, HTTP, HTTPS, RSYNC
- **Batch Processing**: Processes multiple connections concurrently
- **Health Monitoring**: Health check and status endpoints
- **Sync History**: Tracks sync operations in SQLite database
- **Error Handling**: Comprehensive error handling and logging

## Configuration

Environment variables (see `config/settings.py`):

- `SYNC_FREQUENCY`: daily, hourly, weekly (default: daily)
- `SYNC_TIME`: Time for daily/weekly sync (default: 02:00)
- `MAX_FILE_SIZE_MB`: Maximum file size to process (default: 50)
- `BATCH_SIZE`: Number of connections to process concurrently (default: 5)
- `SUPPORTED_EXTENSIONS`: File extensions to sync (default: .txt,.md,.py,.js,.json,.xml,.csv)

## API Endpoints

### Health & Status
- `GET /health`: Health check endpoint
- `GET /status`: Get current sync status and configuration
- `GET /connections`: Get all active connections available for sync
- `GET /history`: Get sync history (query params: limit, days, connection_id)
- `GET /api-docs`: API documentation

### Sync Operations
- `POST /sync`: Trigger manual sync for all connections
- `POST /sync/connection/<id>`: Trigger manual sync for specific connection
- `POST /sync/force`: Force sync even if one is in progress (use with caution)

## API Examples

```bash
# Get API documentation
curl http://localhost:8091/api-docs

# Check health
curl http://localhost:8091/health

# Get current status
curl http://localhost:8091/status

# Get all connections
curl http://localhost:8091/connections

# Trigger sync for all connections
curl -X POST http://localhost:8091/sync

# Sync specific connection
curl -X POST http://localhost:8091/sync/connection/abc-123

# Get sync history (last 10 entries from last 1 day)
curl "http://localhost:8091/history?limit=10&days=1"

# Get sync history for specific connection
curl "http://localhost:8091/history?connection_id=abc-123&limit=5"

# Force sync (use with caution)
curl -X POST http://localhost:8091/sync/force
```

## Deployment

```bash
docker-compose up -d job-remote-host-syncer
```

## Testing

```bash
python test_job.py
```

## Service Architecture

The service consists of:

- **Flask Web Server**: Provides REST API endpoints on port 8091
- **Background Scheduler**: Runs periodic sync jobs based on configuration
- **Syncer Service**: Core business logic for syncing connections
- **Protocol Handlers**: Handle different connection protocols (SSH, SFTP, HTTP, etc.)
- **SQLite Database**: Stores sync history and file states
- **Integration**: Works with MCP service and embedding service

## Monitoring

The service provides comprehensive monitoring through:

- Health check endpoint for container orchestration
- Status endpoint showing current sync state and configuration
- History endpoint for tracking sync operations over time
- Detailed logging with performance metrics
- Connection-specific sync tracking

## Error Handling

- Graceful handling of connection failures
- Retry logic for transient errors
- Comprehensive error logging
- Status tracking for failed operations
- Isolation of connection failures (one failed connection doesn't stop others)
