#!/usr/bin/env python3
"""
Audio Trimmer Utility
Trims audio files based on expected duration to remove XTTS-v2 hallucinations.

XTTS-v2 often adds weird sounds ("aah", "yee", breathing) at the end of audio.
This utility calculates expected audio length based on text and trims excess.

Based on research: https://github.com/coqui-ai/TTS/issues/3277
"""

import sys
import os
import librosa
import soundfile as sf
import numpy as np


def estimate_audio_duration(text, reference_audio_path=None, reference_text=None, sample_rate=24000):
    """
    Estimate expected audio duration based on text length.
    
    If reference audio and text are provided, uses their ratio.
    Otherwise, uses average speaking rate (150 words per minute).
    
    Args:
        text: Input text to estimate duration for
        reference_audio_path: Optional path to reference audio
        reference_text: Optional reference text corresponding to reference audio
        sample_rate: Audio sample rate (default: 24000 for XTTS-v2)
    
    Returns:
        Estimated duration in seconds
    """
    if reference_audio_path and reference_text:
        # Calculate duration based on reference audio/text ratio
        ref_duration = librosa.get_duration(path=reference_audio_path, sr=sample_rate)
        ref_char_count = len(reference_text)
        input_char_count = len(text)
        
        # Estimate based on character ratio
        estimated_duration = ref_duration * (input_char_count / ref_char_count)
    else:
        # Use average speaking rate: ~150 words per minute = 2.5 words per second
        # Average word length: ~5 characters + 1 space = 6 characters per word
        # So: ~15 characters per second
        chars_per_second = 15
        estimated_duration = len(text) / chars_per_second
    
    return estimated_duration


def trim_audio_to_duration(input_audio_path, output_audio_path, target_duration, buffer_percent=25):
    """
    Trim audio file to target duration with buffer.
    
    Args:
        input_audio_path: Path to input audio file
        output_audio_path: Path to save trimmed audio
        target_duration: Target duration in seconds
        buffer_percent: Percentage buffer to add (default: 25%)
    
    Returns:
        Actual trimmed duration in seconds
    """
    # Load audio
    y, sr = librosa.load(input_audio_path, sr=None)
    
    # Calculate target duration with buffer
    buffered_duration = target_duration * (1 + buffer_percent / 100)
    
    # Calculate number of samples
    target_samples = int(buffered_duration * sr)
    
    # Trim audio (don't exceed original length)
    trimmed_audio = y[:min(target_samples, len(y))]
    
    # Save trimmed audio
    sf.write(output_audio_path, trimmed_audio, sr)
    
    # Return actual duration
    actual_duration = len(trimmed_audio) / sr
    return actual_duration


def trim_audio_smart(input_audio_path, output_audio_path, text, buffer_percent=25, 
                     reference_audio_path=None, reference_text=None):
    """
    Smart audio trimming based on text length.
    
    Args:
        input_audio_path: Path to input audio file
        output_audio_path: Path to save trimmed audio
        text: Text that was used to generate the audio
        buffer_percent: Percentage buffer to add (default: 25%)
        reference_audio_path: Optional reference audio for better estimation
        reference_text: Optional reference text for better estimation
    
    Returns:
        dict with trimming statistics
    """
    # Get original audio duration
    original_duration = librosa.get_duration(path=input_audio_path)
    
    # Estimate expected duration
    estimated_duration = estimate_audio_duration(
        text, 
        reference_audio_path=reference_audio_path,
        reference_text=reference_text
    )
    
    # Trim audio
    actual_duration = trim_audio_to_duration(
        input_audio_path,
        output_audio_path,
        estimated_duration,
        buffer_percent=buffer_percent
    )
    
    # Calculate statistics
    trimmed_seconds = original_duration - actual_duration
    trimmed_percent = (trimmed_seconds / original_duration) * 100 if original_duration > 0 else 0
    
    return {
        'original_duration': original_duration,
        'estimated_duration': estimated_duration,
        'actual_duration': actual_duration,
        'trimmed_seconds': trimmed_seconds,
        'trimmed_percent': trimmed_percent,
        'buffer_percent': buffer_percent
    }


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python audio_trimmer.py <input_audio> <output_audio> <text> [buffer_percent]")
        print("Example: python audio_trimmer.py input.wav output.wav 'Hello world' 25")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    text = sys.argv[3]
    buffer_percent = float(sys.argv[4]) if len(sys.argv) > 4 else 25
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"Trimming audio: {input_path}")
    print(f"Text: {text}")
    print(f"Buffer: {buffer_percent}%")
    
    stats = trim_audio_smart(input_path, output_path, text, buffer_percent=buffer_percent)
    
    print(f"\n✅ Audio trimmed successfully!")
    print(f"   Original duration: {stats['original_duration']:.2f}s")
    print(f"   Estimated duration: {stats['estimated_duration']:.2f}s")
    print(f"   Actual duration: {stats['actual_duration']:.2f}s")
    print(f"   Trimmed: {stats['trimmed_seconds']:.2f}s ({stats['trimmed_percent']:.1f}%)")
    print(f"   Output: {output_path}")

