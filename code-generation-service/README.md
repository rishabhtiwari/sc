# Code Generation Service

A specialized service that connects to user code repositories and generates code using existing LLM services. This service analyzes codebases, extracts patterns and styles, and generates contextually appropriate code based on user requirements.

## Features

- **Repository Connection**: Connect to Git repositories, GitHub, GitLab, or local filesystem
- **Code Analysis**: Analyze codebase structure, patterns, dependencies, and coding styles
- **Intelligent Code Generation**: Generate code that follows existing patterns using LLM services
- **Multi-language Support**: Python, Java, JavaScript, TypeScript, Go, Rust, C++, C#, PHP, Ruby, Swift, Kotlin
- **Context-Aware**: Uses repository analysis to generate contextually appropriate code

## Architecture

The service acts as a connector and analyzer that:
1. Connects to user code repositories
2. Analyzes code structure and patterns
3. Uses existing LLM services (llm-service, llm-prompt-generation) for code generation
4. Provides REST API endpoints for integration

## API Endpoints

### Repository Management
- `POST /code/connect` - Connect to a code repository
- `POST /code/analyze` - Analyze a connected repository
- `GET /code/files` - List files in repository
- `GET /code/file` - Get specific file content
- `POST /code/cleanup` - Clean up temporary files

### Code Generation
- `POST /code/generate` - Generate code based on requirements and repository context

### Health & Status
- `GET /health` - Basic health check
- `GET /status` - Detailed service status

## Usage Examples

### 1. Connect to a Git Repository

```bash
curl -X POST http://localhost:8085/code/connect \
  -H "Content-Type: application/json" \
  -d '{
    "type": "git",
    "url": "https://github.com/user/repo.git",
    "branch": "main"
  }'
```

### 2. Connect to Local Repository

```bash
curl -X POST http://localhost:8085/code/connect \
  -H "Content-Type: application/json" \
  -d '{
    "type": "local",
    "path": "/path/to/local/repo"
  }'
```

### 3. Analyze Repository

```bash
curl -X POST http://localhost:8085/code/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "git_123456_myrepo",
    "language": "python"
  }'
```

### 4. Generate Code

```bash
curl -X POST http://localhost:8085/code/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "git_123456_myrepo",
    "requirements": "Create a user authentication class with login and logout methods",
    "language": "python",
    "file_type": "class",
    "context_files": ["auth/base.py", "models/user.py"]
  }'
```

## Configuration

Environment variables:

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8085)
- `LLM_SERVICE_HOST` - LLM service hostname
- `LLM_SERVICE_PORT` - LLM service port
- `LLM_PROMPT_SERVICE_HOST` - LLM prompt service hostname
- `LLM_PROMPT_SERVICE_PORT` - LLM prompt service port
- `MAX_REPO_SIZE_MB` - Maximum repository size (default: 500MB)
- `MAX_FILE_SIZE_KB` - Maximum file size for analysis (default: 1MB)

## Installation & Running

### Using Docker

```bash
# Build and run
./docker-run.sh

# Or using docker-compose
docker-compose up -d
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

## Dependencies

- **External Services**: Requires llm-service and/or llm-prompt-generation services
- **System**: Git (for repository cloning)
- **Python**: Flask, requests, gunicorn

## Supported Repository Types

- **Git**: Any Git repository accessible via HTTPS
- **GitHub**: GitHub repositories (public/private with credentials)
- **GitLab**: GitLab repositories (public/private with credentials)
- **Local**: Local filesystem directories

## Supported Programming Languages

- Python (.py, .pyx, .pyi)
- Java (.java)
- JavaScript (.js, .jsx, .mjs)
- TypeScript (.ts, .tsx)
- Go (.go)
- Rust (.rs)
- C++ (.cpp, .cc, .cxx, .hpp, .hh)
- C (.c, .h)
- C# (.cs)
- PHP (.php)
- Ruby (.rb)
- Swift (.swift)
- Kotlin (.kt, .kts)

## Code Analysis Features

- **Structure Analysis**: Files, directories, dependencies
- **Pattern Extraction**: Common imports, naming conventions
- **Style Analysis**: Indentation, line length, comment patterns
- **Language-Specific Parsing**: AST analysis for Python, regex patterns for others
- **Dependency Detection**: package.json, requirements.txt, pom.xml, etc.

## Security Considerations

- Repository credentials are not stored permanently
- Temporary files are cleaned up automatically
- File size and repository size limits prevent abuse
- Input validation on all endpoints

## Monitoring

- Health check endpoint for service monitoring
- Detailed status endpoint with dependency checks
- Structured logging with configurable levels
- Request/response logging for debugging
