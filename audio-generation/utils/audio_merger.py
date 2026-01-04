#!/usr/bin/env python3
"""
Clean audio merger using pydub
Merges multiple WAV chunks with optional silence between them
"""

import sys
import json
from pydub import AudioSegment
import io

def merge_audio_chunks(audio_buffers, silence_ms=100):
    """
    Merge multiple audio buffers into one with silence between chunks
    
    Args:
        audio_buffers: List of audio data (bytes)
        silence_ms: Milliseconds of silence to add between chunks (default: 100ms)
    
    Returns:
        Merged audio data as bytes
    """
    combined_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=silence_ms)
    
    for i, audio_data in enumerate(audio_buffers):
        # Load WAV from bytes
        audio_chunk = AudioSegment.from_wav(io.BytesIO(audio_data))
        
        # Add chunk to combined audio
        combined_audio += audio_chunk
        
        # Add silence between chunks (but not after the last one)
        if i < len(audio_buffers) - 1:
            combined_audio += silence
    
    # Export to bytes
    output_buffer = io.BytesIO()
    combined_audio.export(output_buffer, format="wav")
    output_buffer.seek(0)
    
    return output_buffer.read()

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: audio_merger.py <silence_ms> [audio files from stdin as JSON array]'
        }))
        sys.exit(1)
    
    silence_ms = int(sys.argv[1])
    
    # Read file paths from stdin as JSON
    input_data = sys.stdin.read().strip()
    
    if not input_data:
        print(json.dumps({'error': 'No input data provided'}))
        sys.exit(1)
    
    try:
        file_paths = json.loads(input_data)
        
        # Read all audio files
        audio_buffers = []
        for file_path in file_paths:
            with open(file_path, 'rb') as f:
                audio_buffers.append(f.read())
        
        # Merge audio
        merged_audio = merge_audio_chunks(audio_buffers, silence_ms)
        
        # Write to stdout (binary)
        sys.stdout.buffer.write(merged_audio)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

