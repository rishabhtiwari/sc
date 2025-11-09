# Audio Generation Factory Service

A factory-based voice generation service supporting multiple TTS (Text-to-Speech) models with persistent model caching.

## Features

- **Factory Pattern**: Easily add new TTS models through the factory system
- **Model Caching**: Downloaded models are cached persistently to avoid re-downloading
- **Multi-language Support**: Support for multiple languages through MMS models
- **RESTful API**: Simple HTTP API for text-to-speech generation
- **Docker Support**: Containerized deployment with volume mounting for model persistence

## Supported Models

### MMS (Massively Multilingual Speech) Models
- **Hindi**: `mms-tts-hin` - Xenova/mms-tts-hin
- **English**: `mms-tts-eng` - Xenova/mms-tts-eng
- **Bengali**: `mms-tts-ben` - Xenova/mms-tts-ben
- **Tamil**: `mms-tts-tam` - Xenova/mms-tts-tam
- **Telugu**: `mms-tts-tel` - Xenova/mms-tts-tel
- **Marathi**: `mms-tts-mar` - Xenova/mms-tts-mar
- **Gujarati**: `mms-tts-guj` - Xenova/mms-tts-guj
- **Kannada**: `mms-tts-kan` - Xenova/mms-tts-kan
- **Malayalam**: `mms-tts-mal` - Xenova/mms-tts-mal
- **Punjabi**: `mms-tts-pan` - Xenova/mms-tts-pan

## API Endpoints

### Core TTS
- `POST /tts` - Generate speech from text
- `GET /health` - Service health check

### Model Management
- `GET /models` - Get loaded models info
- `GET /models/available` - Get all available models
- `GET /models/language/:language` - Get models by language
- `POST /models/load` - Load a new model
- `DELETE /models/:modelKey` - Unload a model

### Cache Management
- `GET /cache/status` - Get model cache status

## Usage Examples

### Generate Speech
```bash
curl -X POST http://localhost:3000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "नमस्ते, यह एक परीक्षण है।", "model": "mms-tts-hin"}'
```

### Load New Model
```bash
curl -X POST http://localhost:3000/models/load \
  -H "Content-Type: application/json" \
  -d '{"modelKey": "mms-tts-eng", "setAsDefault": false}'
```

### Check Cache Status
```bash
curl http://localhost:3000/cache/status
```

## Architecture

### Factory Pattern
- `BaseVoiceModel`: Abstract base class for all voice models
- `MMSVoiceModel`: Implementation for MMS TTS models
- `VoiceModelFactory`: Factory for creating model instances
- `VoiceService`: Service layer managing multiple models

### Model Caching
- Models are cached in `/app/data/models/` directory (mounted from host `./data/models/`)
- Host directory mounting ensures models persist across container rebuilds
- Downloaded models are accessible from host filesystem
- Cache status can be checked via API

## Docker Deployment

### Host Volume Mounting
The service uses host directory mounting for:
- **Model Storage**: `./audio-generation/data/` → `/app/data/` (models persist across rebuilds)
- **Audio Output**: `./audio-generation/public/` → `/app/public/` (generated audio accessible from host)

### Using Docker Compose (Recommended)
```bash
docker-compose up audio-generation-factory
```

### Manual Docker Build
```bash
cd audio-generation
docker build -t audio-generation .
docker run -d --name audio-gen -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/public:/app/public \
  audio-generation
```

## Environment Variables

- `NODE_ENV`: Environment (production/development)
- `PORT`: Service port (default: 3000)
- `MODEL_CACHE_DIR`: Model cache directory (default: /app/data/models)

## File Structure

```
audio-generation/
├── data/
│   └── models/                # Downloaded TTS models (host mounted)
├── public/                    # Generated audio files (host mounted)
├── models/
│   ├── BaseVoiceModel.js      # Abstract base class
│   ├── MMSVoiceModel.js       # MMS model implementation
│   └── VoiceModelFactory.js   # Model factory
├── services/
│   └── VoiceService.js        # Service layer
├── server.js                  # Express server
├── package.json               # Dependencies
├── Dockerfile                 # Docker configuration
├── .gitignore                 # Git ignore patterns
└── test.html                  # Web interface for testing
```

## Adding New Models

1. Create a new model class extending `BaseVoiceModel`
2. Register the model in `VoiceModelFactory.modelConfigs`
3. Update the factory's `createModel` method if needed

## Performance Notes

- First model load downloads from Hugging Face (slower)
- Subsequent loads use cached models (faster)
- Memory usage scales with number of loaded models
- Recommended: 2-4GB RAM, 2 CPU cores

## Key Benefits

1. **Host Volume Persistence**: Models and audio stored in host directories survive container rebuilds
2. **No Re-downloads**: Models cached permanently across container restarts
3. **Host Accessibility**: Easy access to downloaded models and generated audio from host filesystem
4. **Multi-Model Support**: Load multiple languages simultaneously
5. **Factory Extensibility**: Easy to add new TTS providers (Coqui, Bark, etc.)
6. **Resource Efficient**: Only download models when needed
7. **Development Friendly**: Easy to inspect cached models and generated audio files
8. **Production Ready**: Proper error handling, health checks, logging
