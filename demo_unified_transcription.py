#!/usr/bin/env python3
"""
Demo script showing how to use the unified transcription and sync functionality
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def demo_transcription_only():
    """Demo: Pure audio transcription without lyrics"""
    print("🎤 Demo 1: Pure Audio Transcription")
    print("=" * 50)
    
    audio_file = "./data/transcribe_vocal/quality_test_vocals_clean.wav"
    
    cmd = f"""python src/lyrics/transcribe_vocal.py "{audio_file}" \
--model_size base \
--device cpu \
--output_dir ./demo_output/transcription"""
    
    print(f"Command: {cmd}")
    print("\nThis will:")
    print("- Transcribe the audio using Whisper AI")
    print("- Generate .txt, .srt, .lrc, and .json files")
    print("- Include word-level timestamps")
    
    return cmd

def demo_lyrics_sync():
    """Demo: Lyrics synchronization with existing lyrics"""
    print("\n🎵 Demo 2: Lyrics Synchronization")
    print("=" * 50)
    
    audio_file = "./data/transcribe_vocal/quality_test_vocals_clean.wav"
    lyrics_file = "./quality_test_vocals_clean.txt"
    
    cmd = f"""python src/lyrics/transcribe_vocal.py "{audio_file}" \
--lyrics_file "{lyrics_file}" \
--model_size base \
--device cpu \
--similarity_threshold 0.6 \
--output_dir ./demo_output/synchronized"""
    
    print(f"Command: {cmd}")
    print("\nThis will:")
    print("- Load existing lyrics from text file")
    print("- Transcribe audio with word-level timestamps")
    print("- Align lyrics with audio using fuzzy matching")
    print("- Generate synchronized .lrc, .srt, .json files")
    print("- Show confidence scores for each matched line")
    
    return cmd

def show_usage():
    """Show usage examples and features"""
    print("🚀 Unified Audio Transcription & Lyrics Sync")
    print("=" * 60)
    print("\nFeatures:")
    print("✅ Combines transcription and sync into one process")
    print("✅ Uses Whisper AI for accurate speech recognition")
    print("✅ Word-level timestamps for precise synchronization")
    print("✅ Fuzzy text matching for lyrics alignment")
    print("✅ Multiple output formats (TXT, SRT, LRC, JSON)")
    print("✅ Confidence scoring for alignment quality")
    print("✅ Support for various audio formats")
    print("✅ Automatic language detection")
    
    print("\n📋 Available Arguments:")
    print("  audio_file              Path to audio file (required)")
    print("  --lyrics_file          Path to lyrics file (optional, enables sync mode)")
    print("  --model_size           Whisper model size (tiny, base, small, medium, large-v3)")
    print("  --device               Processing device (auto, cpu, cuda)")
    print("  --language             Language code (en, ko, es, etc.)")
    print("  --similarity_threshold Text matching threshold (0.0-1.0)")
    print("  --output_dir           Output directory")
    
    cmd1 = demo_transcription_only()
    cmd2 = demo_lyrics_sync()
    
    print("\n🔧 To run the demos:")
    print(f"\n1. Transcription only:\n   {cmd1}")
    print(f"\n2. Lyrics synchronization:\n   {cmd2}")
    
    print("\n📁 Output files will include:")
    print("  - .txt: Plain text transcript")
    print("  - .srt: Subtitle format with timestamps")
    print("  - .lrc: Lyrics format for music players")
    print("  - .json: Detailed data with word timings")

if __name__ == "__main__":
    show_usage()
