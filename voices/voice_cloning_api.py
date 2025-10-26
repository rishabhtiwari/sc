#!/usr/bin/env python3
"""
Voice Cloning API Service
A FastAPI wrapper that accepts file uploads and forwards requests to XTTS API server.
"""

import os
import tempfile
import shutil
import requests
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

app = FastAPI(title="Voice Cloning API", version="1.0.0")

# Configuration
XTTS_API_URL = "http://localhost:8000"  # Internal XTTS server
TEMP_DIR = "/tmp/voice_cloning"
OUTPUT_DIR = "/app/output"

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        response = requests.get(f"{XTTS_API_URL}/speakers", timeout=5)
        xtts_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        xtts_status = "unreachable"
    
    return {
        "status": "healthy",
        "xtts_server": xtts_status,
        "version": "1.0.0"
    }

@app.post("/clone_voice")
async def clone_voice(
    text: str = Form(..., description="Text to convert to speech"),
    language: str = Form(default="en", description="Language code (e.g., 'en', 'es', 'fr')"),
    speaker_wav: UploadFile = File(..., description="Reference voice audio file"),
    output_filename: Optional[str] = Form(default=None, description="Output filename (optional)")
):
    """
    Clone voice from uploaded audio file and generate speech from text.
    
    Args:
        text: Text to convert to speech
        language: Language code
        speaker_wav: Uploaded audio file for voice reference
        output_filename: Optional output filename
    
    Returns:
        Generated audio file
    """
    
    # Generate unique filename if not provided
    if not output_filename:
        output_filename = f"cloned_voice_{uuid.uuid4().hex[:8]}.wav"
    
    # Ensure output filename has .wav extension
    if not output_filename.endswith('.wav'):
        output_filename += '.wav'
    
    temp_speaker_path = None
    
    try:
        # Validate uploaded file
        if not speaker_wav.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Check file extension
        allowed_extensions = ['.wav', '.mp3', '.flac', '.ogg']
        file_ext = Path(speaker_wav.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        temp_speaker_path = os.path.join(TEMP_DIR, f"speaker_{uuid.uuid4().hex}.wav")
        with open(temp_speaker_path, "wb") as buffer:
            shutil.copyfileobj(speaker_wav.file, buffer)
        
        # Copy speaker file to XTTS speakers directory
        speakers_dir = "/app/speakers"
        os.makedirs(speakers_dir, exist_ok=True)
        speaker_filename = f"temp_speaker_{uuid.uuid4().hex}.wav"
        speaker_path = os.path.join(speakers_dir, speaker_filename)
        shutil.copy2(temp_speaker_path, speaker_path)
        
        # Prepare request to XTTS API
        xtts_request = {
            "text": text,
            "speaker_wav": speaker_filename,
            "language": language,
            "file_name_or_path": output_filename
        }
        
        # Call XTTS API
        response = requests.post(
            f"{XTTS_API_URL}/tts_to_file",
            json=xtts_request,
            timeout=1800  # 30 minutes timeout for long processing
        )
        
        if response.status_code != 200:
            error_detail = response.text if response.text else "XTTS API error"
            raise HTTPException(
                status_code=response.status_code,
                detail=f"XTTS API error: {error_detail}"
            )
        
        # Check if output file was created
        output_file_path = os.path.join(OUTPUT_DIR, output_filename)
        if not os.path.exists(output_file_path):
            raise HTTPException(
                status_code=500,
                detail="Voice cloning completed but output file not found"
            )
        
        # Return the generated audio file
        return FileResponse(
            path=output_file_path,
            media_type="audio/wav",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Cleanup temporary files
        if temp_speaker_path and os.path.exists(temp_speaker_path):
            try:
                os.remove(temp_speaker_path)
            except:
                pass
        
        # Cleanup speaker file from XTTS directory
        try:
            if 'speaker_path' in locals() and os.path.exists(speaker_path):
                os.remove(speaker_path)
        except:
            pass

@app.post("/clone_voice_json")
async def clone_voice_json(
    text: str = Form(...),
    language: str = Form(default="en"),
    speaker_wav: UploadFile = File(...),
    output_filename: Optional[str] = Form(default=None)
):
    """
    Same as clone_voice but returns JSON response with file info instead of file download.
    """
    
    # Generate unique filename if not provided
    if not output_filename:
        output_filename = f"cloned_voice_{uuid.uuid4().hex[:8]}.wav"
    
    # Ensure output filename has .wav extension
    if not output_filename.endswith('.wav'):
        output_filename += '.wav'
    
    temp_speaker_path = None
    
    try:
        # Validate uploaded file
        if not speaker_wav.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Save uploaded file temporarily
        temp_speaker_path = os.path.join(TEMP_DIR, f"speaker_{uuid.uuid4().hex}.wav")
        with open(temp_speaker_path, "wb") as buffer:
            shutil.copyfileobj(speaker_wav.file, buffer)
        
        # Copy speaker file to XTTS speakers directory
        speakers_dir = "/app/speakers"
        os.makedirs(speakers_dir, exist_ok=True)
        speaker_filename = f"temp_speaker_{uuid.uuid4().hex}.wav"
        speaker_path = os.path.join(speakers_dir, speaker_filename)
        shutil.copy2(temp_speaker_path, speaker_path)
        
        # Prepare request to XTTS API
        xtts_request = {
            "text": text,
            "speaker_wav": speaker_filename,
            "language": language,
            "file_name_or_path": output_filename
        }
        
        # Call XTTS API
        response = requests.post(
            f"{XTTS_API_URL}/tts_to_file",
            json=xtts_request,
            timeout=1800
        )
        
        if response.status_code != 200:
            error_detail = response.text if response.text else "XTTS API error"
            raise HTTPException(
                status_code=response.status_code,
                detail=f"XTTS API error: {error_detail}"
            )
        
        # Check if output file was created
        output_file_path = os.path.join(OUTPUT_DIR, output_filename)
        if not os.path.exists(output_file_path):
            raise HTTPException(
                status_code=500,
                detail="Voice cloning completed but output file not found"
            )
        
        # Get file info
        file_size = os.path.getsize(output_file_path)
        
        return JSONResponse({
            "status": "success",
            "message": "Voice cloning completed successfully",
            "output_file": output_filename,
            "file_size": file_size,
            "download_url": f"/download/{output_filename}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Cleanup temporary files
        if temp_speaker_path and os.path.exists(temp_speaker_path):
            try:
                os.remove(temp_speaker_path)
            except:
                pass
        
        # Cleanup speaker file from XTTS directory
        try:
            if 'speaker_path' in locals() and os.path.exists(speaker_path):
                os.remove(speaker_path)
        except:
            pass

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated audio file"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Voice Cloning API Service",
        "version": "1.0.0",
        "endpoints": {
            "POST /clone_voice": "Upload audio file and text to generate voice-cloned speech (returns audio file)",
            "POST /clone_voice_json": "Same as above but returns JSON response",
            "GET /download/{filename}": "Download generated audio file",
            "GET /health": "Health check"
        },
        "usage": {
            "curl_example": "curl -X POST 'http://localhost:5003/clone_voice' -F 'text=\"Your text here\"' -F 'language=\"en\"' -F 'speaker_wav=@/path/to/voice.wav' --output cloned.wav"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)
