#!/usr/bin/env python3
"""Test script to verify Bark GPU performance"""

import os
import time
import torch

# Force GPU usage
os.environ["SUNO_OFFLOAD_CPU"] = "False"
os.environ["SUNO_USE_SMALL_MODELS"] = "False"

print("=" * 60)
print("BARK GPU PERFORMANCE TEST")
print("=" * 60)

# Check CUDA
print(f"\n🔍 CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"🔢 CUDA version: {torch.version.cuda}")
else:
    print("⚠️  WARNING: CUDA not available!")

# Import Bark
print("\n📦 Importing Bark...")
from bark import SAMPLE_RATE, generate_audio, preload_models

# Preload models
print("\n🔄 Preloading Bark models...")
start_time = time.time()
preload_models(
    text_use_gpu=True,
    coarse_use_gpu=True,
    fine_use_gpu=True
)
load_time = time.time() - start_time
print(f"✅ Models loaded in {load_time:.2f} seconds")

# Check GPU memory after loading
if torch.cuda.is_available():
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    reserved = torch.cuda.memory_reserved(0) / 1024**3
    print(f"💾 GPU Memory allocated: {allocated:.2f} GB")
    print(f"💾 GPU Memory reserved: {reserved:.2f} GB")

# Generate short audio
print("\n🎤 Generating audio for 'Hello world'...")
start_time = time.time()
audio = generate_audio("Hello world", history_prompt="v2/en_speaker_0")
gen_time = time.time() - start_time
print(f"✅ Audio generated in {gen_time:.2f} seconds")
print(f"🎵 Audio length: {len(audio)} samples ({len(audio)/SAMPLE_RATE:.2f} seconds)")

# Check GPU memory after generation
if torch.cuda.is_available():
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    reserved = torch.cuda.memory_reserved(0) / 1024**3
    print(f"💾 GPU Memory allocated: {allocated:.2f} GB")
    print(f"💾 GPU Memory reserved: {reserved:.2f} GB")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

