#!/usr/bin/env python3
"""
Demo script for creating synchronized lyrics video players.
This script demonstrates how to use the lyrics video player with your sync data.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from gui.lyrics_video_player import create_lyrics_video_player

def demo_lyrics_player():
    """Demonstrate creating a lyrics video player."""
    
    print("🎵 Synchronized Lyrics Video Player Demo")
    print("=" * 50)
    
    # Define file paths
    base_dir = Path(__file__).parent
    audio_file = base_dir / "all-music-of-hip-hop_eminem-ft-rihanna-love-the-way-you-lie.mp3"
    sync_json = base_dir / "sync_output" / "all-music-of-hip-hop_eminem-ft-rihanna-love-the-way-you-lie_synced.json"
    
    # Check if files exist
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        print("Please ensure the audio file is in the project root directory.")
        return
    
    if not sync_json.exists():
        print(f"❌ Sync JSON file not found: {sync_json}")
        print("Please run the lyrics synchronization first to generate sync data.")
        return
    
    print(f"🎤 Audio file: {audio_file.name}")
    print(f"📊 Sync data: {sync_json.name}")
    
    try:
        # Create the lyrics video player
        result = create_lyrics_video_player(
            audio_path=str(audio_file),
            sync_json_path=str(sync_json),
            title="Love The Way You Lie - Synchronized Lyrics",
            output_dir="./player_output",
            auto_open=True,
            server_port=8080
        )
        
        print(f"\n🎉 Player created successfully!")
        print(f"🌐 Access at: {result}")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ Error creating player: {e}")

def create_custom_player():
    """Create a custom player with user input."""
    
    print("\n🎬 Create Custom Lyrics Player")
    print("-" * 40)
    
    # Get user input
    audio_path = input("📁 Enter path to audio file: ").strip().strip('"')
    sync_path = input("📊 Enter path to sync JSON file: ").strip().strip('"')
    title = input("🎵 Enter player title (optional): ").strip()
    
    if not title:
        title = "Synchronized Lyrics Player"
    
    try:
        result = create_lyrics_video_player(
            audio_path=audio_path,
            sync_json_path=sync_path,
            title=title,
            auto_open=True
        )
        
        print(f"\n✅ Custom player created: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_features():
    """Show the features of the lyrics video player."""
    
    print("\n🌟 Lyrics Video Player Features")
    print("=" * 40)
    print("🎵 Real-time lyrics synchronization")
    print("🔤 Word-level highlighting (when available)")
    print("⏯️  Audio/Video playback controls")
    print("🔍 Click lyrics to seek to that time")
    print("📱 Responsive design for mobile/desktop")
    print("⌨️  Keyboard shortcuts (Space, Arrow keys)")
    print("🎚️  Adjustable font size")
    print("📊 Sync quality indicators")
    print("🎨 Beautiful animated interface")
    print("🌐 Runs in any modern web browser")
    
    print("\n🎮 Controls:")
    print("   Space: Play/Pause")
    print("   ← →: Skip 5 seconds")
    print("   Click lyrics: Jump to that time")
    print("   Click progress bar: Seek")

def main():
    """Main demo function."""
    
    print("🎵 Synchronized Lyrics Video Player")
    print("🚀 Interactive Demo Script")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. 🎬 Demo with existing files")
        print("2. 🎨 Create custom player")
        print("3. 🌟 Show features")
        print("4. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            demo_lyrics_player()
        elif choice == "2":
            create_custom_player()
        elif choice == "3":
            show_features()
        elif choice == "4":
            print("👋 Thanks for using the Lyrics Video Player Demo!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
