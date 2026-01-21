#!/usr/bin/env python3
"""
VAD (Voice Activity Detection) Audio Trimmer
Uses Silero VAD to detect where speech ends and trim trailing artifacts
"""

import sys
import json
import torch
import torchaudio
import warnings
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")


def load_silero_vad():
    """
    Load Silero VAD model
    Returns: (model, utils)
    """
    try:
        # Load Silero VAD model from torch hub
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        return model, utils
    except Exception as e:
        print(f"Error loading Silero VAD: {e}", file=sys.stderr)
        return None, None


def trim_audio_with_vad(audio_path, output_path=None, threshold=0.5, min_silence_duration_ms=300):
    """
    Trim audio using VAD to remove trailing artifacts
    
    Args:
        audio_path: Path to input audio file
        output_path: Path to save trimmed audio (optional, defaults to overwriting input)
        threshold: VAD confidence threshold (0.0-1.0, default: 0.5)
        min_silence_duration_ms: Minimum silence duration to consider as end (default: 300ms)
    
    Returns:
        dict with success status and trimmed audio path
    """
    try:
        # Load VAD model
        model, utils = load_silero_vad()
        if model is None:
            return {
                'success': False,
                'error': 'Failed to load Silero VAD model'
            }
        
        # Extract utils
        (get_speech_timestamps, _, read_audio, *_) = utils
        
        # Read audio file
        wav = read_audio(audio_path, sampling_rate=16000)
        
        # Get speech timestamps
        speech_timestamps = get_speech_timestamps(
            wav,
            model,
            threshold=threshold,
            min_silence_duration_ms=min_silence_duration_ms,
            return_seconds=False
        )
        
        if not speech_timestamps:
            # No speech detected - return original
            return {
                'success': True,
                'trimmed': False,
                'message': 'No speech detected, keeping original audio',
                'output_path': audio_path
            }
        
        # Get the end of the last speech segment
        last_speech_end = speech_timestamps[-1]['end']
        
        # Load original audio at its native sample rate
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Calculate trim point (convert from 16kHz to native sample rate)
        trim_point = int(last_speech_end * sample_rate / 16000)
        
        # Add small padding (100ms) to avoid cutting off the last word
        padding_samples = int(0.1 * sample_rate)
        trim_point = min(trim_point + padding_samples, waveform.shape[1])
        
        # Trim the audio
        trimmed_waveform = waveform[:, :trim_point]
        
        # Calculate how much was trimmed
        original_duration = waveform.shape[1] / sample_rate
        trimmed_duration = trimmed_waveform.shape[1] / sample_rate
        trimmed_ms = (original_duration - trimmed_duration) * 1000
        
        # Save trimmed audio
        if output_path is None:
            output_path = audio_path
        
        torchaudio.save(output_path, trimmed_waveform, sample_rate)
        
        return {
            'success': True,
            'trimmed': True,
            'original_duration_ms': original_duration * 1000,
            'trimmed_duration_ms': trimmed_duration * 1000,
            'removed_ms': trimmed_ms,
            'output_path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """CLI interface for VAD trimmer"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: vad_trimmer.py <audio_file> [output_file] [threshold] [min_silence_ms]'
        }))
        sys.exit(1)
    
    audio_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    min_silence_ms = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    
    result = trim_audio_with_vad(audio_path, output_path, threshold, min_silence_ms)
    print(json.dumps(result))


if __name__ == '__main__':
    main()

