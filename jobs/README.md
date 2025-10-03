# Jobs System

This folder contains scheduled jobs that run periodically to sync data and maintain system state.

## Job Structure

Each job is organized in its own folder with the following structure:
```
jobs/
├── job-name/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py (main job script)
│   ├── config/
│   │   └── settings.py
│   ├── services/
│   │   └── job_service.py
│   └── utils/
│       └── logger.py
```

## Available Jobs

### remote-host-syncer
- **Purpose**: Syncs data from connected remote host MCP servers to embedding service
- **Frequency**: Daily (configurable)
- **Description**: Fetches files and documents from active remote host connections and indexes them in the embedding service for RAG functionality

## Running Jobs

### Development
```bash
cd jobs/remote-host-syncer
python app.py
```

### Production (Docker)
```bash
docker-compose up -d job-remote-host-syncer
```

## Job Configuration

Jobs can be configured via environment variables or config files. Each job has its own configuration in the `config/settings.py` file.

## Scheduling

Jobs can be run:
1. **On-demand**: Execute manually for testing
2. **Cron-based**: Using system cron or container scheduling
3. **Event-driven**: Triggered by webhooks or API calls

## Monitoring

Jobs log their activities and can be monitored through:
- Log files in each job's `logs/` directory
- Health check endpoints (if implemented)
- Integration with monitoring systems
