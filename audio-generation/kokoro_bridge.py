#!/usr/bin/env python3
"""
Kokoro TTS Python Bridge
This script provides a bridge between Node.js and the Python Kokoro library
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

# Also suppress torch warnings specifically
import logging
logging.getLogger().setLevel(logging.ERROR)

def generate_speech(text, voice="af_heart", speed=1.0, output_path=None):
    """
    Generate speech using Kokoro TTS

    Args:
        text (str): Text to convert to speech
        voice (str): Voice to use (default: af_heart)
        speed (float): Speech speed (0.5 to 2.0, default: 1.0)
        output_path (str): Path to save the audio file

    Returns:
        dict: Result with success status and file path
    """
    try:
        # Import Kokoro (will be installed in Docker)
        from kokoro import KPipeline
        import soundfile as sf
        import torch

        print(f"🔄 Initializing Kokoro pipeline with voice: {voice}, speed: {speed}", file=sys.stderr)

        # Initialize pipeline based on voice
        if voice.startswith('af_') or voice.startswith('am_'):
            lang_code = 'a'  # American English
        elif voice.startswith('bf_') or voice.startswith('bm_'):
            lang_code = 'b'  # British English
        else:
            lang_code = 'a'  # Default to American English

        pipeline = KPipeline(lang_code=lang_code)

        print(f"🎤 Generating speech for text: {text[:50]}...", file=sys.stderr)

        # Generate audio with custom speed
        generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
        
        # Collect all audio segments
        audio_segments = []
        for i, (gs, ps, audio) in enumerate(generator):
            audio_segments.append(audio)
            print(f"📝 Generated segment {i}: {gs[:30]}...", file=sys.stderr)
        
        if not audio_segments:
            return {
                "success": False,
                "error": "No audio segments generated"
            }
        
        # Concatenate audio segments if multiple
        if len(audio_segments) == 1:
            final_audio = audio_segments[0]
        else:
            import numpy as np
            final_audio = np.concatenate(audio_segments)
        
        # Save audio file
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            sf.write(output_path, final_audio, 24000)
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

            return {
                "success": True,
                "file_path": output_path,
                "duration": len(final_audio) / 24000,
                "sample_rate": 24000
            }
        else:
            return {
                "success": True,
                "audio_data": final_audio.tolist(),
                "sample_rate": 24000
            }
            
    except ImportError as e:
        return {
            "success": False,
            "error": f"Kokoro library not installed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Speech generation failed: {str(e)}"
        }

def main():
    parser = argparse.ArgumentParser(description='Kokoro TTS Bridge')
    parser.add_argument('--text', required=True, help='Text to convert to speech')
    parser.add_argument('--voice', default='af_heart', help='Voice to use')
    parser.add_argument('--speed', type=float, default=1.0, help='Speech speed (0.5 to 2.0)')
    parser.add_argument('--output', required=True, help='Output file path')

    args = parser.parse_args()

    # Redirect all stdout to stderr except for our final JSON output
    # Also redirect subprocess stdout/stderr to avoid package installation messages
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Create a null device to suppress all output during library initialization
    import subprocess
    devnull = open(os.devnull, 'w')

    try:
        # Redirect both stdout and stderr to suppress all library messages
        sys.stdout = devnull
        sys.stderr = devnull

        # Also set environment variables to suppress pip and other tool output
        os.environ['PIP_QUIET'] = '1'
        os.environ['PYTHONWARNINGS'] = 'ignore'

        result = generate_speech(args.text, args.voice, args.speed, args.output)

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
