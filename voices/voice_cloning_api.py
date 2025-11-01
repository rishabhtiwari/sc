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
import re
import time
import wave
import asyncio
from pathlib import Path
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

app = FastAPI(title="Voice Cloning API", version="1.0.0")

# Configuration
XTTS_API_URL = "http://localhost:8000"  # Internal XTTS server
TEMP_DIR = "/tmp/voice_cloning"
OUTPUT_DIR = "/app/output"
CHUNKS_DIR = "/app/chunks"

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)

# Text chunking utilities
def split_text_into_sentences(text: str, max_length: int = 200) -> List[str]:
    """
    Split text into sentences with maximum length limit.

    Args:
        text (str): Input text to split
        max_length (int): Maximum characters per chunk

    Returns:
        list: List of text chunks
    """
    # First split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding this sentence would exceed max_length, save current chunk
        if len(current_chunk) + len(sentence) > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def concatenate_audio_files(audio_files: List[str], output_path: str) -> bool:
    """
    Concatenate multiple WAV files into a single file.

    Args:
        audio_files (list): List of WAV file paths in order
        output_path (str): Output path for concatenated file

    Returns:
        bool: Success status
    """
    if not audio_files:
        print("Error: No audio files provided for concatenation")
        return False

    try:
        print(f"Attempting to concatenate {len(audio_files)} audio files")

        # Check if all files exist
        missing_files = []
        for i, audio_file in enumerate(audio_files):
            if not os.path.exists(audio_file):
                missing_files.append(f"File {i}: {audio_file}")
            else:
                file_size = os.path.getsize(audio_file)
                print(f"File {i}: {audio_file} (size: {file_size} bytes)")

        if missing_files:
            print(f"Error: Missing audio files: {missing_files}")
            return False

        # Read first file to get parameters
        print(f"Reading first file: {audio_files[0]}")
        with wave.open(audio_files[0], 'rb') as first_wave:
            params = first_wave.getparams()
            frames = first_wave.readframes(first_wave.getnframes())
            print(f"First file params: channels={params.nchannels}, sample_width={params.sampwidth}, framerate={params.framerate}, frames={params.nframes}")

        # Read and concatenate remaining files
        for i, audio_file in enumerate(audio_files[1:], 1):
            print(f"Processing file {i}: {audio_file}")
            try:
                with wave.open(audio_file, 'rb') as wave_file:
                    file_params = wave_file.getparams()
                    print(f"File {i} params: channels={file_params.nchannels}, sample_width={file_params.sampwidth}, framerate={file_params.framerate}, frames={file_params.nframes}")

                    # Check if parameters match
                    if (file_params.nchannels != params.nchannels or
                        file_params.sampwidth != params.sampwidth or
                        file_params.framerate != params.framerate):
                        print(f"Warning: File {i} has different audio parameters than first file")

                    frames += wave_file.readframes(wave_file.getnframes())
            except Exception as e:
                print(f"Error reading file {i} ({audio_file}): {e}")
                return False

        # Write concatenated audio
        print(f"Writing concatenated audio to: {output_path}")
        with wave.open(output_path, 'wb') as output_wave:
            output_wave.setparams(params)
            output_wave.writeframes(frames)

        # Verify output file was created
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"Concatenation successful! Output file size: {output_size} bytes")
            return True
        else:
            print("Error: Output file was not created")
            return False

    except Exception as e:
        print(f"Error concatenating audio files: {e}")
        import traceback
        traceback.print_exc()
        return False

async def process_single_text(text: str, language: str, speaker_filename: str, output_filename: str):
    """Process text without chunking (regular processing)."""
    xtts_request = {
        "text": text,
        "speaker_wav": speaker_filename,
        "language": language,
        "file_name_or_path": output_filename
    }

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

    output_file_path = os.path.join(OUTPUT_DIR, output_filename)
    if not os.path.exists(output_file_path):
        raise HTTPException(
            status_code=500,
            detail="Voice cloning completed but output file not found"
        )

    return FileResponse(
        path=output_file_path,
        media_type="audio/wav",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename={output_filename}"}
    )

async def process_chunk(text: str, language: str, speaker_filename: str,
                       output_filename: str, speaker_id: str, is_first_chunk: bool = False):
    """Process a single text chunk."""
    try:
        if is_first_chunk:
            # First chunk: create speaker embedding
            xtts_request = {
                "text": text,
                "speaker_wav": speaker_filename,
                "language": language,
                "file_name_or_path": output_filename
            }
        else:
            # Subsequent chunks: use cached speaker embedding
            # Note: This assumes XTTS API supports speaker caching by ID
            # If not supported, we'll fall back to using speaker_wav
            xtts_request = {
                "text": text,
                "speaker_wav": speaker_filename,  # Fallback to speaker_wav
                "language": language,
                "file_name_or_path": output_filename
            }

        response = requests.post(
            f"{XTTS_API_URL}/tts_to_file",
            json=xtts_request,
            timeout=1800  # 30 minutes timeout for chunks (same as regular processing)
        )

        if response.status_code == 200:
            output_file_path = os.path.join(OUTPUT_DIR, output_filename)
            return os.path.exists(output_file_path)
        else:
            print(f"XTTS API error for chunk: {response.text}")
            return False

    except Exception as e:
        print(f"Error processing chunk: {e}")
        return False

def process_chunk_sync(text: str, language: str, speaker_filename: str,
                      output_filename: str, speaker_id: str, is_first_chunk: bool = False):
    """Synchronous version of process_chunk for use with ThreadPoolExecutor."""
    try:
        if is_first_chunk:
            xtts_request = {
                "text": text,
                "speaker_wav": speaker_filename,
                "language": language,
                "file_name_or_path": output_filename
            }
        else:
            xtts_request = {
                "text": text,
                "speaker_wav": speaker_filename,
                "language": language,
                "file_name_or_path": output_filename
            }

        response = requests.post(
            f"{XTTS_API_URL}/tts_to_file",
            json=xtts_request,
            timeout=1800  # 30 minutes timeout for chunks (same as regular processing)
        )

        if response.status_code == 200:
            output_file_path = os.path.join(OUTPUT_DIR, output_filename)
            return os.path.exists(output_file_path)
        else:
            print(f"XTTS API error for chunk: {response.text}")
            return False

    except Exception as e:
        print(f"Error processing chunk: {e}")
        return False

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

@app.post("/clone_voice_chunked")
async def clone_voice_chunked(
    text: str = Form(..., description="Text to convert to speech (will be split into chunks)"),
    language: str = Form(default="en", description="Language code (e.g., 'en', 'es', 'fr')"),
    speaker_wav: UploadFile = File(..., description="Reference voice audio file"),
    output_filename: Optional[str] = Form(default=None, description="Output filename (optional)"),
    max_chunk_length: int = Form(default=200, description="Maximum characters per chunk"),
    max_workers: int = Form(default=3, description="Maximum parallel workers for chunk processing"),
    enable_chunking: bool = Form(default=True, description="Enable text chunking for faster processing")
):
    """
    Clone voice using chunked text processing for faster generation of long texts.

    Args:
        text: Text to convert to speech (will be automatically chunked)
        language: Language code
        speaker_wav: Uploaded audio file for voice reference
        output_filename: Optional output filename
        max_chunk_length: Maximum characters per text chunk
        max_workers: Number of parallel workers for chunk processing
        enable_chunking: Whether to enable chunking (if False, uses regular processing)

    Returns:
        Generated audio file (concatenated from chunks)
    """

    # Generate unique filename if not provided
    if not output_filename:
        output_filename = f"chunked_voice_{uuid.uuid4().hex[:8]}.wav"

    # Ensure output filename has .wav extension
    if not output_filename.endswith('.wav'):
        output_filename += '.wav'

    temp_speaker_path = None
    speaker_path = None
    chunk_files = []

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

        # Check if chunking should be used
        if not enable_chunking or len(text) <= max_chunk_length:
            # Use regular processing for short texts
            return await process_single_text(text, language, speaker_filename, output_filename)

        # Split text into chunks
        chunks = split_text_into_sentences(text, max_chunk_length)
        print(f"Split text into {len(chunks)} chunks")

        # Generate unique IDs for this request to avoid conflicts with other concurrent jobs
        request_id = uuid.uuid4().hex[:12]  # Longer ID for better uniqueness
        speaker_id = f"chunked_speaker_{request_id}"

        # Process first chunk to create speaker embedding
        first_chunk_filename = f"chunk_{request_id}_000.wav"
        first_chunk_result = await process_chunk(
            chunks[0], language, speaker_filename, first_chunk_filename,
            speaker_id, is_first_chunk=True
        )

        if not first_chunk_result:
            raise HTTPException(status_code=500, detail="Failed to process first chunk")

        chunk_files.append(os.path.join(OUTPUT_DIR, first_chunk_filename))

        # Process remaining chunks in parallel using cached speaker embedding
        if len(chunks) > 1:
            remaining_chunk_tasks = []
            chunk_filenames = []  # Keep track of expected filenames in order

            for i, chunk_text in enumerate(chunks[1:], 1):
                chunk_filename = f"chunk_{request_id}_{i:03d}.wav"
                chunk_filenames.append(chunk_filename)  # Store in order
                remaining_chunk_tasks.append({
                    'text': chunk_text,
                    'language': language,
                    'speaker_filename': speaker_filename,
                    'output_filename': chunk_filename,
                    'speaker_id': speaker_id,
                    'is_first_chunk': False,
                    'chunk_index': i  # Add index for ordering
                })

            # Process chunks in parallel
            chunk_results = {}  # Store results by chunk index
            with ThreadPoolExecutor(max_workers=min(max_workers, len(remaining_chunk_tasks))) as executor:
                future_to_chunk = {
                    executor.submit(
                        process_chunk_sync,
                        task['text'], task['language'], task['speaker_filename'],
                        task['output_filename'], task['speaker_id'], task['is_first_chunk']
                    ): task for task in remaining_chunk_tasks
                }

                for future in as_completed(future_to_chunk):
                    task = future_to_chunk[future]
                    try:
                        result = future.result()
                        chunk_results[task['chunk_index']] = {
                            'success': result,
                            'filename': task['output_filename']
                        }
                        if result:
                            print(f"Successfully processed chunk {task['chunk_index']}: {task['output_filename']}")
                        else:
                            print(f"Failed to process chunk {task['chunk_index']}: {task['output_filename']}")
                    except Exception as e:
                        print(f"Error processing chunk {task['chunk_index']} ({task['output_filename']}): {e}")
                        chunk_results[task['chunk_index']] = {
                            'success': False,
                            'filename': task['output_filename']
                        }

            # Add chunk files in correct order (1, 2, 3, ...)
            for i in range(1, len(chunks)):
                if i in chunk_results and chunk_results[i]['success']:
                    chunk_files.append(os.path.join(OUTPUT_DIR, chunk_results[i]['filename']))
                else:
                    print(f"Warning: Chunk {i} failed or missing")

        print(f"Final chunk files in order: {[os.path.basename(f) for f in chunk_files]}")

        # Concatenate all chunk files
        final_output_path = os.path.join(OUTPUT_DIR, output_filename)
        print(f"Attempting to concatenate {len(chunk_files)} chunk files for request {request_id}")
        print(f"Chunk files: {[os.path.basename(f) for f in chunk_files]}")

        concatenation_success = concatenate_audio_files(chunk_files, final_output_path)
        if not concatenation_success:
            print(f"Concatenation failed for request {request_id} - preserving chunk files for debugging")
            raise HTTPException(status_code=500, detail="Failed to concatenate audio chunks")

        # Verify final file was created
        if not os.path.exists(final_output_path):
            raise HTTPException(status_code=500, detail="Final concatenated file not found")

        # Return the generated audio file
        response = FileResponse(
            path=final_output_path,
            media_type="audio/wav",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )

        # Clean up chunk files only on success
        try:
            for filename in os.listdir(OUTPUT_DIR):
                if filename.startswith(f"chunk_{request_id}_"):
                    chunk_file_path = os.path.join(OUTPUT_DIR, filename)
                    try:
                        if os.path.exists(chunk_file_path):
                            os.remove(chunk_file_path)
                            print(f"Cleaned up successful chunk file: {filename}")
                    except Exception as e:
                        print(f"Failed to cleanup chunk file {filename}: {e}")
        except Exception as e:
            print(f"Error during successful chunk cleanup: {e}")

        return response

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
        if speaker_path and os.path.exists(speaker_path):
            try:
                os.remove(speaker_path)
            except:
                pass

        # Note: Chunk files are cleaned up in success case above
        # On error, chunk files are preserved for debugging

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
            "POST /clone_voice_chunked": "Upload audio file and long text for chunked processing (faster for long texts)",
            "GET /download/{filename}": "Download generated audio file",
            "GET /health": "Health check"
        },
        "usage": {
            "curl_example": "curl -X POST 'http://localhost:5003/clone_voice' -F 'text=\"Your text here\"' -F 'language=\"en\"' -F 'speaker_wav=@/path/to/voice.wav' --output cloned.wav",
            "chunked_example": "curl -X POST 'http://localhost:5003/clone_voice_chunked' -F 'text=\"Your very long text here...\"' -F 'language=\"en\"' -F 'speaker_wav=@/path/to/voice.wav' -F 'max_chunk_length=200' -F 'max_workers=3' --output chunked.wav"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)
