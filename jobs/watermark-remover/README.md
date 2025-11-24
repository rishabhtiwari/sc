# Logo/Watermark Remover Service

AI-powered logo and watermark removal service using Lama-Cleaner.

## Architecture

This service consists of two components:

1. **Lama-Cleaner** (Port 7860) - Core AI engine for image inpainting
2. **Logo Remover API** (Port 8096) - Python Flask wrapper for easy integration

## Features

✅ **Automatic Logo Detection** - AI automatically detects and removes logos  
✅ **Manual Mask Support** - Provide custom masks for precise removal  
✅ **Batch Processing** - Process multiple images at once  
✅ **Multiple Formats** - Supports PNG, JPG, JPEG, WebP  
✅ **REST API** - Easy integration with other services  

## Quick Start

### 1. Deploy Services

```bash
# Build and start both services
docker-compose up -d lama-cleaner job-logo-remover

# Check status
docker-compose ps lama-cleaner job-logo-remover

# View logs
docker-compose logs -f job-logo-remover
```

### 2. Access Services

- **Lama-Cleaner Web UI**: http://localhost:7860
- **Logo Remover API**: http://localhost:8096

## API Usage

### Remove Logo from Single Image

```bash
curl -X POST http://localhost:8096/remove-logo \
  -F "file=@/path/to/image.jpg" \
  -F "auto_detect=true" \
  --output cleaned_image.jpg
```

### Remove Logo with Custom Mask

```bash
curl -X POST http://localhost:8096/remove-logo \
  -F "file=@/path/to/image.jpg" \
  -F "mask=@/path/to/mask.png" \
  -F "auto_detect=false" \
  --output cleaned_image.jpg
```

### Batch Processing

```bash
curl -X POST http://localhost:8096/remove-logo-batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

### Health Check

```bash
curl http://localhost:8096/health
```

## Python Integration Example

```python
import requests

# Remove logo from image
with open('image_with_logo.jpg', 'rb') as f:
    files = {'file': f}
    data = {'auto_detect': 'true'}
    
    response = requests.post(
        'http://localhost:8096/remove-logo',
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        with open('cleaned_image.jpg', 'wb') as out:
            out.write(response.content)
        print("✅ Logo removed successfully!")
    else:
        print(f"❌ Error: {response.json()}")
```

## Integration with Video Generator

You can integrate this with your video-generator service:

```python
# In video-generator service
import requests

def remove_logo_from_image(image_path):
    """Remove logo from news image before video generation"""
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'auto_detect': 'true'}
        
        response = requests.post(
            'http://ichat-logo-remover:8096/remove-logo',
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            # Save cleaned image
            cleaned_path = image_path.replace('.jpg', '_cleaned.jpg')
            with open(cleaned_path, 'wb') as out:
                out.write(response.content)
            return cleaned_path
        else:
            raise Exception(f"Logo removal failed: {response.json()}")
```

## Configuration

### Environment Variables

- `FLASK_PORT`: API server port (default: 8096)
- `LAMA_CLEANER_URL`: Lama-Cleaner service URL (default: http://ichat-lama-cleaner:7860)
- `OUTPUT_DIR`: Output directory for cleaned images (default: /app/output)

### Lama-Cleaner Models

Available models (can be changed in docker-compose.yml):
- `lama` - Default, best quality (recommended)
- `ldm` - Latent Diffusion Model
- `zits` - ZITS inpainting
- `mat` - MAT inpainting
- `fcf` - Fast Context Fill

To change model:
```yaml
command: ["lama-cleaner", "--model=ldm", "--device=cpu", "--port=7860", "--host=0.0.0.0"]
```

## Output

Cleaned images are saved in:
- Container: `/app/output/`
- Host: `./jobs/watermark-remover/public/`

## Performance

- **CPU Mode**: ~5-10 seconds per image
- **GPU Mode**: ~1-2 seconds per image (requires GPU setup)

To enable GPU:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## Troubleshooting

### Service not starting
```bash
# Check logs
docker-compose logs lama-cleaner
docker-compose logs job-logo-remover

# Restart services
docker-compose restart lama-cleaner job-logo-remover
```

### Out of memory
Increase memory limits in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase from 4G
```

### Slow processing
- Use GPU mode if available
- Reduce image resolution before processing
- Use faster models (fcf, mat)

## Advanced Usage

### Using Lama-Cleaner Web UI

1. Open http://localhost:7860
2. Upload image
3. Draw mask over logo/watermark
4. Click "Inpaint" to remove

### Custom Mask Creation

Create a mask image where:
- **White pixels (255)** = Areas to remove
- **Black pixels (0)** = Areas to keep

```python
from PIL import Image, ImageDraw

# Create mask
img = Image.open('image.jpg')
mask = Image.new('L', img.size, 0)
draw = ImageDraw.Draw(mask)

# Draw white rectangle over logo area
draw.rectangle([100, 100, 300, 200], fill=255)

mask.save('mask.png')
```

## License

This service uses Lama-Cleaner which is licensed under Apache 2.0.

## Credits

- **Lama-Cleaner**: https://github.com/Sanster/lama-cleaner
- **LaMa Model**: https://github.com/advimman/lama

