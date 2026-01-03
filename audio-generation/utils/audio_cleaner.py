#!/usr/bin/env python3
"""
Advanced Audio Cleaner and Merger for TTS Chunks
Provides professional-quality audio merging with:
- Volume normalization
- Crossfading for smooth transitions
- Natural silence/breathing pauses
- Optional noise reduction
"""

import sys
import json
import io
from pydub import AudioSegment
from pydub.effects import normalize

def merge_and_clean_audio(audio_buffers, silence_ms=200, crossfade_ms=50, enable_normalization=True):
    """
    Merge multiple audio buffers with professional cleaning and enhancement
    
    Args:
        audio_buffers: List of audio data (bytes)
        silence_ms: Milliseconds of silence to add between chunks for natural breathing (default: 200ms)
        crossfade_ms: Milliseconds of crossfade for smooth transitions (default: 50ms)
        enable_normalization: Whether to normalize volume (default: True)
    
    Returns:
        Merged and cleaned audio data as bytes
    """
    if not audio_buffers:
        raise ValueError("No audio buffers provided")
    
    final_audio = AudioSegment.empty()
    
    # Create silence for natural breathing pauses between sentences
    silence = AudioSegment.silent(duration=silence_ms)
    
    print(f"🎵 Merging {len(audio_buffers)} audio chunks with cleaning...", file=sys.stderr)
    print(f"   - Silence between chunks: {silence_ms}ms", file=sys.stderr)
    print(f"   - Crossfade duration: {crossfade_ms}ms", file=sys.stderr)
    normalization_status = "enabled ✓" if enable_normalization else "disabled ✗"
    print(f"   - Normalization: {normalization_status}", file=sys.stderr)
    
    for i, audio_data in enumerate(audio_buffers):
        # Load WAV from bytes
        chunk = AudioSegment.from_wav(io.BytesIO(audio_data))
        
        print(f"   📦 Processing chunk {i+1}/{len(audio_buffers)} ({len(chunk)}ms)", file=sys.stderr)
        
        # First chunk: just add it
        if len(final_audio) == 0:
            final_audio = chunk
        else:
            # Add silence before the chunk for natural breathing
            chunk_with_silence = silence + chunk
            
            # Append with crossfade to smooth the join and prevent clicks
            # This creates a natural flow like a single breath
            final_audio = final_audio.append(chunk_with_silence, crossfade=crossfade_ms)
    
    # Final overall cleanup: Normalize volume to prevent sudden jumps
    if enable_normalization:
        print("   🔊 Normalizing volume...", file=sys.stderr)
        final_audio = normalize(final_audio)
    
    print(f"   ✅ Final audio duration: {len(final_audio)}ms", file=sys.stderr)
    
    # Export to bytes
    output_buffer = io.BytesIO()
    final_audio.export(output_buffer, format="wav")
    output_buffer.seek(0)
    
    return output_buffer.read()


def merge_and_clean_audio_advanced(audio_buffers, silence_ms=200, crossfade_ms=50, 
                                   enable_normalization=True, enable_noise_reduction=False):
    """
    Advanced version with optional noise reduction (requires noisereduce library)
    
    Args:
        audio_buffers: List of audio data (bytes)
        silence_ms: Milliseconds of silence between chunks (default: 200ms)
        crossfade_ms: Milliseconds of crossfade (default: 50ms)
        enable_normalization: Whether to normalize volume (default: True)
        enable_noise_reduction: Whether to apply noise reduction (default: False)
    
    Returns:
        Merged and cleaned audio data as bytes
    """
    # First merge with basic cleaning
    merged_audio_bytes = merge_and_clean_audio(
        audio_buffers, 
        silence_ms=silence_ms, 
        crossfade_ms=crossfade_ms,
        enable_normalization=enable_normalization
    )
    
    # Apply noise reduction if enabled
    if enable_noise_reduction:
        try:
            import noisereduce as nr
            import numpy as np
            from scipy.io import wavfile
            
            print("   🎚️  Applying noise reduction...", file=sys.stderr)
            
            # Load audio for noise reduction
            audio = AudioSegment.from_wav(io.BytesIO(merged_audio_bytes))
            
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Apply noise reduction
            reduced_noise = nr.reduce_noise(y=samples, sr=audio.frame_rate)
            
            # Convert back to AudioSegment
            cleaned_audio = AudioSegment(
                reduced_noise.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            
            # Export cleaned audio
            output_buffer = io.BytesIO()
            cleaned_audio.export(output_buffer, format="wav")
            output_buffer.seek(0)
            
            print("   ✅ Noise reduction applied", file=sys.stderr)
            return output_buffer.read()
            
        except ImportError:
            print("   ⚠️  noisereduce library not available, skipping noise reduction", file=sys.stderr)
            return merged_audio_bytes
        except Exception as e:
            print(f"   ⚠️  Noise reduction failed: {e}, using basic cleaning", file=sys.stderr)
            return merged_audio_bytes
    
    return merged_audio_bytes


def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: audio_cleaner.py <silence_ms> [crossfade_ms] [normalize] [denoise]'
        }))
        sys.exit(1)
    
    # Parse arguments
    silence_ms = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    crossfade_ms = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    enable_normalization = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    enable_noise_reduction = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False
    
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
        
        # Merge and clean audio
        if enable_noise_reduction:
            merged_audio = merge_and_clean_audio_advanced(
                audio_buffers, 
                silence_ms=silence_ms,
                crossfade_ms=crossfade_ms,
                enable_normalization=enable_normalization,
                enable_noise_reduction=True
            )
        else:
            merged_audio = merge_and_clean_audio(
                audio_buffers,
                silence_ms=silence_ms,
                crossfade_ms=crossfade_ms,
                enable_normalization=enable_normalization
            )
        
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

