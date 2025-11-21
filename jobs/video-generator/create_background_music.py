#!/usr/bin/env python3
"""
Create a simple royalty-free background music for news videos

This script generates a subtle, professional background music track
suitable for news content using basic audio synthesis.
"""

import numpy as np
from scipy.io import wavfile
import os


def create_news_background_music(duration=60, sample_rate=44100):
    """
    Create professional news-style background music for news videos

    This creates a modern, structured news underscore with:
    - Rhythmic pulse (ticking) for urgency and time
    - Minor/suspended intervals for professional, serious tone
    - Clear low frequencies to avoid interfering with voice
    - Electronic/modern texture with harmonics

    Args:
        duration: Duration in seconds (default: 60 seconds)
        sample_rate: Audio sample rate (default: 44100 Hz)

    Returns:
        numpy array with audio data
    """
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create the base audio
    audio = np.zeros_like(t)

    # TWEAK 1: Add a rhythmic pulse (ticking) - 100 BPM for news urgency
    pulse_freq_bpm = 100  # 100 beats per minute
    pulse_freq_hz = pulse_freq_bpm / 60  # ~1.67 Hz

    # Create a sharp, percussive pulse using short bursts
    pulse = np.zeros_like(t)
    pulse_interval = sample_rate / pulse_freq_hz

    # Generate short, sharp clicks at the interval
    for i in range(0, len(t), int(pulse_interval)):
        # Short burst of high frequency (digital click)
        burst_duration = int(sample_rate * 0.01)  # 10 ms burst
        if i + burst_duration < len(t):
            pulse[i:i+burst_duration] = np.sin(2 * np.pi * 3000 * t[i:i+burst_duration])

    # Apply a very low volume to the pulse
    audio += pulse * 0.02

    # TWEAK 2: Use modern frequencies with minor/tense intervals for professional news feel
    # Changed from major chord (C-E-G-C) to minor/suspended intervals (A-C-F-A)
    frequencies = [
        440.00,   # A4 (Base)
        523.25,   # C5 (Minor Third Tones)
        698.46,   # F5 (Suspension/Fourth)
        880.00,   # A5 (Octave)
    ]

    for i, freq in enumerate(frequencies):
        # Use gentle amplitude - noticeable but not overpowering
        amplitude = 0.08 / (i + 1)  # Gentle, decreasing for each harmonic

        # Add harmonics to make the tone sound more modern/electronic (not pure sine wave)
        synth_tone = 0.8 * np.sin(2 * np.pi * freq * t) + \
                     0.15 * np.sin(2 * np.pi * 2 * freq * t) + \
                     0.05 * np.sin(2 * np.pi * 3 * freq * t)

        # Add gentle envelope with slow attack/decay
        envelope = np.sin(2 * np.pi * 0.05 * t) * 0.5 + 0.5  # Slow breathing effect
        audio += amplitude * synth_tone * envelope

    # Add subtle white noise for texture (like soft air)
    noise = np.random.normal(0, 0.01, len(t))  # Gentle noise
    audio += noise

    # TWEAK 3: Reduce low-frequency rumble to clear space for voice (80-200 Hz range)
    # Raised frequency from 110 Hz to 150 Hz and reduced amplitude significantly
    rumble_freq = 150.0  # Higher frequency, less chest rumble
    rumble = 0.01 * np.sin(2 * np.pi * rumble_freq * t)  # Much lower amplitude
    rumble *= (1 + 0.2 * np.sin(2 * np.pi * 0.03 * t))  # Slow modulation
    audio += rumble

    # Apply longer fade in and fade out for smoother transitions
    fade_duration = 3.0  # 3 seconds fade
    fade_samples = int(sample_rate * fade_duration)

    # Fade in
    fade_in = np.linspace(0, 1, fade_samples)
    audio[:fade_samples] *= fade_in

    # Fade out
    fade_out = np.linspace(1, 0, fade_samples)
    audio[-fade_samples:] *= fade_out

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    # Scale to 16-bit integer range with balanced volume
    # Keep it at about 25% of maximum possible volume - noticeable but gentle
    audio = (audio * 32767 * 0.25).astype(np.int16)

    return audio


def main():
    """Generate background music file"""
    print("🎵 Generating royalty-free background music for news videos...")
    
    # Create assets directory if it doesn't exist
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Generate 60 seconds of music (will be looped as needed)
    duration = 60  # seconds
    sample_rate = 44100  # Hz
    
    print(f"   Duration: {duration} seconds")
    print(f"   Sample rate: {sample_rate} Hz")
    
    # Generate the audio
    audio_data = create_news_background_music(duration, sample_rate)
    
    # Save as WAV file
    output_path = os.path.join(assets_dir, 'background_music.wav')
    wavfile.write(output_path, sample_rate, audio_data)
    
    # Get file size
    file_size = os.path.getsize(output_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"✅ Background music created successfully!")
    print(f"   File: {output_path}")
    print(f"   Size: {file_size_mb:.2f} MB")
    print(f"   Format: WAV (16-bit, {sample_rate} Hz)")
    print(f"   Duration: {duration} seconds")
    print(f"   Type: Subtle ambient pad (royalty-free)")


if __name__ == '__main__':
    main()

