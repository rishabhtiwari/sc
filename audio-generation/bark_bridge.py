#!/usr/bin/env python3
"""
Bark TTS Python Bridge
This script provides a bridge between Node.js and the Python Bark library
Supports voice cloning, emotions, music, and multi-language TTS
"""

import sys
import json
import os
import argparse
import warnings
from pathlib import Path

# Suppress ALL warnings to avoid JSON parsing issues
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Also suppress logging
import logging
logging.getLogger().setLevel(logging.ERROR)

def generate_speech(text, speaker="v2/en_speaker_0", output_path=None):
    """
    Generate speech using Bark TTS

    Args:
        text (str): Text to convert to speech (supports [laughs], [sighs], etc.)
        speaker (str): Speaker preset or custom voice prompt (default: v2/en_speaker_0)
        output_path (str): Path to save the audio file

    Returns:
        dict: Result with success status and file path
    """
    try:
        # Import Bark (will be installed in Docker)
        from bark import SAMPLE_RATE, generate_audio, preload_models
        from scipy.io.wavfile import write as write_wav
        import numpy as np
        import torch

        # Check GPU availability
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🖥️  Using device: {device}", file=sys.stderr)
        if device == 'cuda':
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)}", file=sys.stderr)
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB", file=sys.stderr)
        else:
            print(f"⚠️  CUDA not available, using CPU (will be very slow)", file=sys.stderr)

        print(f"🔄 Initializing Bark with speaker: {speaker}", file=sys.stderr)

        # Set environment variable for GPU usage
        if device == 'cuda':
            os.environ['SUNO_OFFLOAD_CPU'] = 'False'  # Use GPU
            os.environ['SUNO_USE_SMALL_MODELS'] = 'False'  # Use full models for better quality
        else:
            os.environ['SUNO_OFFLOAD_CPU'] = 'True'  # Offload to CPU
            os.environ['SUNO_USE_SMALL_MODELS'] = 'True'  # Use small models for faster CPU inference

        # Preload models on first use (cached after that)
        print(f"📦 Loading Bark models (this may take a few minutes on first run)...", file=sys.stderr)
        preload_models(
            text_use_gpu=device == 'cuda',
            coarse_use_gpu=device == 'cuda',
            fine_use_gpu=device == 'cuda'
        )
        print(f"✅ Bark models loaded on {device.upper()}", file=sys.stderr)

        print(f"🎤 Generating speech for text: {text[:50]}...", file=sys.stderr)

        # Generate audio
        # Bark automatically handles:
        # - [laughs], [sighs], [gasps], [clears throat]
        # - ♪ music ♪
        # - CAPITALIZATION for emphasis
        # - ... or — for hesitations
        audio_array = generate_audio(
            text,
            history_prompt=speaker
        )

        if audio_array is None or len(audio_array) == 0:
            return {
                "success": False,
                "error": "No audio generated"
            }

        print(f"🎵 Generated audio: {len(audio_array)} samples at {SAMPLE_RATE}Hz", file=sys.stderr)

        # Save audio file
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Normalize audio to prevent clipping
            audio_array = np.clip(audio_array, -1.0, 1.0)
            
            # Convert to int16 for WAV format
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            write_wav(output_path, SAMPLE_RATE, audio_int16)
            print(f"💾 Audio saved to: {output_path}", file=sys.stderr)

            # Verify file was created and has content
            if not os.path.exists(output_path):
                return {
                    "success": False,
                    "error": f"Audio file was not created at: {output_path}"
                }

            file_size = os.path.getsize(output_path)
            if file_size == 0:
                return {
                    "success": False,
                    "error": f"Generated audio file is empty: {output_path}"
                }

            print(f"✅ File verified: {output_path} ({file_size} bytes)", file=sys.stderr)

            duration = len(audio_array) / SAMPLE_RATE

            return {
                "success": True,
                "file_path": output_path,
                "duration": duration,
                "sample_rate": SAMPLE_RATE,
                "samples": len(audio_array)
            }
        else:
            return {
                "success": True,
                "audio_data": audio_array.tolist(),
                "sample_rate": SAMPLE_RATE
            }
            
    except ImportError as e:
        return {
            "success": False,
            "error": f"Bark library not installed: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Speech generation failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def main():
    parser = argparse.ArgumentParser(description='Bark TTS Bridge')
    parser.add_argument('--text', required=True, help='Text to convert to speech')
    parser.add_argument('--speaker', default='v2/en_speaker_0', help='Speaker preset or voice prompt')
    parser.add_argument('--output', required=True, help='Output file path')

    args = parser.parse_args()

    # Redirect all stdout to stderr except for our final JSON output
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Create a null device to suppress all output during library initialization
    devnull = open(os.devnull, 'w')

    try:
        # Redirect both stdout and stderr to suppress all library messages
        sys.stdout = devnull
        sys.stderr = devnull

        # Set environment variables to suppress output
        os.environ['PYTHONWARNINGS'] = 'ignore'
        # Note: GPU/CPU settings are handled inside generate_speech()

        result = generate_speech(args.text, args.speaker, args.output)

        # Restore stdout and output clean JSON
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        devnull.close()

        print(json.dumps(result))

        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)
    except Exception as e:
        # Restore stdout/stderr and output error JSON
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        devnull.close()

        error_result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()

