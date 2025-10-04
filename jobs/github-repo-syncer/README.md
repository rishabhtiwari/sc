# GitHub Repository Syncer Job

A scheduled job service that syncs GitHub repositories to the embedding service for RAG (Retrieval-Augmented Generation) functionality.

## Overview

This service:
- Fetches GitHub repositories from connected MCP tokens
- Clones repositories and processes source code files
- Sends file content to the embedding service for indexing
- Tracks sync history and job progress
- Provides REST API for manual triggers and monitoring

## Features

- **Scheduled Syncing**: Configurable daily/hourly/weekly sync schedules
- **Manual Triggers**: REST API endpoints for on-demand syncing
- **Progress Tracking**: Real-time job progress and status monitoring
- **Concurrent Processing**: Parallel repository and file processing
- **File Filtering**: Smart filtering of supported file types
- **Error Handling**: Robust error handling with retry mechanisms
- **Cancellation Support**: Ability to cancel running sync jobs

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNC_FREQUENCY` | `daily` | Sync frequency: daily, hourly, weekly |
| `SYNC_TIME` | `03:00` | Time to run daily sync (HH:MM format) |
| `MAX_FILE_SIZE_MB` | `10` | Maximum file size to process (MB) |
| `BATCH_SIZE` | `50` | Number of files to process per batch |
| `MAX_CONCURRENT_REPOS` | `3` | Max repositories to sync concurrently |
| `MAX_CONCURRENT_FILES` | `10` | Max files to process concurrently per repo |
| `CLONE_DEPTH` | `1` | Git clone depth (1 for shallow clone) |
| `HEALTH_CHECK_PORT` | `8092` | Port for health check server |

### Service URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVICE_URL` | `http://localhost:8089` | MCP service URL |
| `API_SERVER_URL` | `http://localhost:8080` | API server URL |
| `EMBEDDING_SERVICE_URL` | `http://localhost:8085` | Embedding service URL |

## Supported File Types

The service processes common source code and configuration files:

- **Programming Languages**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, etc.
- **Web Technologies**: `.html`, `.css`, `.scss`, `.vue`, `.jsx`, etc.
- **Configuration**: `.json`, `.yaml`, `.xml`, `.toml`, `.env`, etc.
- **Documentation**: `.md`, `.rst`, `.txt`, etc.
- **Database**: `.sql`, `.graphql`, etc.

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - Current sync status and configuration
- `GET /api-docs` - API documentation

### Repository Management
- `GET /repositories` - List all active repositories
- `POST /sync` - Trigger sync for all repositories
- `POST /sync/repository/<id>` - Trigger sync for specific repository

### Job Management
- `GET /job/<id>` - Get job status by ID
- `POST /job/<id>/cancel` - Cancel a specific job
- `GET /jobs/active` - Get all active jobs

## Usage Examples

### Trigger Manual Sync
```bash
# Sync all repositories
curl -X POST http://localhost:8092/sync

# Sync specific repository
curl -X POST http://localhost:8092/sync/repository/github_token123_repo456
```

### Check Status
```bash
# Health check
curl http://localhost:8092/health

# Get sync status
curl http://localhost:8092/status

# List repositories
curl http://localhost:8092/repositories
```

### Monitor Jobs
```bash
# Get job status
curl http://localhost:8092/job/abc-123-def

# Cancel job
curl -X POST http://localhost:8092/job/abc-123-def/cancel

# List active jobs
curl http://localhost:8092/jobs/active
```

## Docker Deployment

### Build Image
```bash
docker build -t github-repo-syncer .
```

### Run Container
```bash
docker run -d \
  --name github-repo-syncer \
  -p 8092:8092 \
  -e SYNC_FREQUENCY=daily \
  -e SYNC_TIME=03:00 \
  -e DOCKER_ENV=true \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  github-repo-syncer
```

## Integration with Job Framework

This service is part of the larger job framework and integrates with:

- **MCP Service**: Gets GitHub repository information and tokens
- **Embedding Service**: Sends processed file content for indexing
- **API Server**: Provides unified API access
- **Remote Host Syncer**: Complementary syncing service for remote hosts

## Database Schema

### sync_history
Tracks sync operations and their results.

### file_sync_state
Tracks individual file processing state.

### job_instances
Tracks job execution and progress (shared with other job services).

## Logging

The service provides structured logging with:
- Sync events and progress
- Performance metrics
- Error tracking
- GitHub API call monitoring

Logs are written to both console and file (`./logs/github-repo-syncer.log`).

## Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MCP_SERVICE_URL=http://localhost:8089
export EMBEDDING_SERVICE_URL=http://localhost:8085

# Run the service
python app.py
```

### Testing
The service includes comprehensive error handling and logging for debugging sync issues.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Service   │    │  GitHub Repos   │    │ Embedding Svc   │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ Get Tokens/Repos     │ Clone & Process      │ Index Content
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                GitHub Repository Syncer                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Scheduler  │  │ Job Manager │  │    File Processor       │  │
│  │             │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    SQLite Database                          │  │
│  │  • sync_history  • file_sync_state  • job_instances       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```
