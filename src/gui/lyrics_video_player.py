"""
Synchronized Lyrics Video Player
Creates a video player with real-time highlighted lyrics based on synced timestamps.

This module creates an HTML5 video player with synchronized lyrics display,
highlighting words/phrases as they are sung in the audio/video.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import argparse
import webbrowser
import http.server
import socketserver
from threading import Thread
import time

class LyricsVideoPlayer:
    """Creates an HTML5 video player with synchronized lyrics display."""
    
    def __init__(self, output_dir: str = "./player_output"):
        """
        Initialize the lyrics video player.
        
        Args:
            output_dir: Directory to save the player files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_sync_data(self, sync_json_path: str) -> Dict[str, Any]:
        """Load synchronized lyrics data from JSON file."""
        with open(sync_json_path, 'r', encoding='utf-8') as f:
            sync_data = json.load(f)
        
        print(f"📖 Loaded sync data: {len(sync_data['segments'])} segments")
        return sync_data
    
    def generate_html_player(self, 
                           audio_path: str, 
                           sync_json_path: str,
                           video_path: Optional[str] = None,
                           title: str = "Synchronized Lyrics Player") -> str:
        """
        Generate HTML5 player with synchronized lyrics.
        
        Args:
            audio_path: Path to audio file
            sync_json_path: Path to synchronized lyrics JSON
            video_path: Optional path to video file
            title: Title for the player
            
        Returns:
            Path to generated HTML file
        """
        print("🎬 Generating HTML5 lyrics player...")
        
        # Load sync data
        sync_data = self.load_sync_data(sync_json_path)
        
        # Convert file paths to relative paths for web serving
        audio_file = Path(audio_path).name
        video_file = Path(video_path).name if video_path else None
        
        # Copy media files to output directory
        import shutil
        shutil.copy2(audio_path, self.output_dir / audio_file)
        if video_path and os.path.exists(video_path):
            shutil.copy2(video_path, self.output_dir / video_file)
        
        # Generate HTML content
        html_content = self._create_html_template(
            audio_file, sync_data, video_file, title
        )
        
        # Save HTML file
        html_path = self.output_dir / "lyrics_player.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML player generated: {html_path}")
        return str(html_path)
    
    def _create_html_template(self, 
                            audio_file: str, 
                            sync_data: Dict[str, Any],
                            video_file: Optional[str] = None,
                            title: str = "Synchronized Lyrics Player") -> str:
        """Create the HTML template for the lyrics player."""
        
        # Convert sync data to JavaScript format
        segments_js = self._convert_segments_to_js(sync_data['segments'])
        
        # Determine if we're using video or audio
        media_element = self._create_media_element(audio_file, video_file)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="player-container">
        <div class="header">
            <h1>{title}</h1>
            <div class="controls">
                <button id="playPauseBtn" class="control-btn">▶️ Play</button>
                <button id="rewindBtn" class="control-btn">⏪ -10s</button>
                <button id="forwardBtn" class="control-btn">⏩ +10s</button>
                <span class="time-display">
                    <span id="currentTime">0:00</span> / <span id="duration">0:00</span>
                </span>
            </div>
        </div>
        
        <div class="media-container">
            {media_element}
            <div class="progress-container">
                <div class="progress-bar">
                    <div id="progressFill" class="progress-fill"></div>
                    <div id="progressHandle" class="progress-handle"></div>
                </div>
            </div>
        </div>
        
        <div class="lyrics-container">
            <div id="lyricsDisplay" class="lyrics-display">
                <div class="lyrics-placeholder">🎵 Lyrics will appear here when audio starts 🎵</div>
            </div>
            <div class="lyrics-controls">
                <label>
                    <input type="checkbox" id="autoScroll" checked> Auto-scroll lyrics
                </label>
                <label>
                    Font size: <input type="range" id="fontSizeSlider" min="12" max="32" value="18">
                </label>
            </div>
        </div>
        
        <div class="info-panel">
            <div class="sync-info">
                <strong>Sync Quality:</strong>
                <span id="syncQuality">Loading...</span>
            </div>
            <div class="segment-info">
                <strong>Current Segment:</strong>
                <span id="currentSegment">-</span> / <span id="totalSegments">{len(sync_data['segments'])}</span>
            </div>
        </div>
    </div>

    <script>
        // Synchronized lyrics data
        const syncData = {segments_js};
        
        {self._get_javascript_code()}
    </script>
</body>
</html>"""
        
        return html_template
    
    def _create_media_element(self, audio_file: str, video_file: Optional[str]) -> str:
        """Create the appropriate media element (video or audio)."""
        if video_file:
            return f"""
            <video id="mediaPlayer" class="media-player" controls>
                <source src="{video_file}" type="video/mp4">
                <source src="{audio_file}" type="audio/mpeg">
                Your browser does not support the video element.
            </video>
            """
        else:
            return f"""
            <audio id="mediaPlayer" class="media-player" controls>
                <source src="{audio_file}" type="audio/mpeg">
                <source src="{audio_file}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
            <div class="audio-visualizer">
                <div class="wave-container">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
            </div>
            """
    
    def _convert_segments_to_js(self, segments: List[Dict]) -> str:
        """Convert segments data to JavaScript format."""
        js_segments = []
        
        for segment in segments:
            js_segment = {
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'text': segment['text'],
                'confidence': segment.get('confidence', 0.0),
                'word_timings': segment.get('word_timings', [])
            }
            js_segments.append(js_segment)
        
        return json.dumps(js_segments, indent=2)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the player."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        
        .player-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .control-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 16px;
        }
        
        .control-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        
        .time-display {
            font-size: 18px;
            font-weight: bold;
            margin-left: 20px;
        }
        
        .media-container {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .media-player {
            width: 100%;
            max-width: 800px;
            border-radius: 10px;
        }
        
        .audio-visualizer {
            margin-top: 20px;
            padding: 20px;
        }
        
        .wave-container {
            display: flex;
            justify-content: center;
            align-items: end;
            gap: 4px;
            height: 60px;
        }
        
        .wave-bar {
            width: 6px;
            background: linear-gradient(to top, #ff6b6b, #4ecdc4);
            border-radius: 3px;
            animation: wave 1.5s ease-in-out infinite;
        }
        
        .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.3s; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; }
        .wave-bar:nth-child(6) { animation-delay: 0.5s; }
        .wave-bar:nth-child(7) { animation-delay: 0.6s; }
        .wave-bar:nth-child(8) { animation-delay: 0.7s; }
        
        @keyframes wave {
            0%, 100% { height: 10px; }
            50% { height: 40px; }
        }
        
        .progress-container {
            margin-top: 15px;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
            position: relative;
            cursor: pointer;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s ease;
        }
        
        .progress-handle {
            position: absolute;
            top: -3px;
            width: 12px;
            height: 12px;
            background: white;
            border-radius: 50%;
            cursor: pointer;
            transform: translateX(-50%);
            left: 0%;
        }
        
        .lyrics-container {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .lyrics-display {
            min-height: 300px;
            max-height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .lyrics-placeholder {
            text-align: center;
            font-size: 18px;
            color: rgba(255,255,255,0.7);
            margin-top: 100px;
        }
        
        .lyric-line {
            margin: 15px 0;
            padding: 10px;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-size: 18px;
            line-height: 1.5;
        }
        
        .lyric-line.current {
            background: rgba(255,255,255,0.2);
            transform: scale(1.02);
            border-left: 4px solid #4ecdc4;
        }
        
        .lyric-line.past {
            opacity: 0.6;
        }
        
        .lyric-line.future {
            opacity: 0.8;
        }
        
        .word-highlight {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            padding: 2px 4px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            transition: all 0.2s ease;
        }
        
        .lyrics-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .lyrics-controls label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
        }
        
        .lyrics-controls input[type="range"] {
            width: 100px;
        }
        
        .info-panel {
            display: flex;
            justify-content: space-between;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .info-panel > div {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        @media (max-width: 768px) {
            .player-container {
                padding: 10px;
            }
            
            .controls {
                flex-direction: column;
                gap: 10px;
            }
            
            .time-display {
                margin-left: 0;
            }
            
            .lyrics-controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .info-panel {
                flex-direction: column;
            }
        }
        """
    
    def _get_javascript_code(self) -> str:
        """Get JavaScript code for the player functionality."""
        return """
        class LyricsPlayer {
            constructor() {
                this.mediaPlayer = document.getElementById('mediaPlayer');
                this.lyricsDisplay = document.getElementById('lyricsDisplay');
                this.currentSegmentIndex = -1;
                this.currentWordIndex = -1;
                this.autoScroll = true;
                
                this.initializePlayer();
                this.setupEventListeners();
                this.displaySyncQuality();
            }
            
            initializePlayer() {
                // Initialize lyrics display
                this.renderLyrics();
                
                // Set up time update
                this.mediaPlayer.addEventListener('timeupdate', () => {
                    this.updateLyrics();
                    this.updateProgress();
                });
                
                // Set up duration display
                this.mediaPlayer.addEventListener('loadedmetadata', () => {
                    this.updateDuration();
                });
            }
            
            setupEventListeners() {
                // Play/Pause button
                document.getElementById('playPauseBtn').addEventListener('click', () => {
                    this.togglePlayPause();
                });
                
                // Rewind button
                document.getElementById('rewindBtn').addEventListener('click', () => {
                    this.mediaPlayer.currentTime = Math.max(0, this.mediaPlayer.currentTime - 10);
                });
                
                // Forward button
                document.getElementById('forwardBtn').addEventListener('click', () => {
                    this.mediaPlayer.currentTime = Math.min(this.mediaPlayer.duration, this.mediaPlayer.currentTime + 10);
                });
                
                // Auto-scroll checkbox
                document.getElementById('autoScroll').addEventListener('change', (e) => {
                    this.autoScroll = e.target.checked;
                });
                
                // Font size slider
                document.getElementById('fontSizeSlider').addEventListener('input', (e) => {
                    this.updateFontSize(e.target.value);
                });
                
                // Progress bar click
                document.querySelector('.progress-bar').addEventListener('click', (e) => {
                    this.seekToPosition(e);
                });
                
                // Keyboard shortcuts
                document.addEventListener('keydown', (e) => {
                    this.handleKeyboard(e);
                });
            }
            
            renderLyrics() {
                this.lyricsDisplay.innerHTML = '';
                
                syncData.forEach((segment, index) => {
                    const lyricLine = document.createElement('div');
                    lyricLine.className = 'lyric-line future';
                    lyricLine.id = `line-${index}`;
                    lyricLine.textContent = segment.text;
                    
                    // Add confidence indicator
                    const confidence = Math.round(segment.confidence * 100);
                    lyricLine.title = `Confidence: ${confidence}%`;
                    
                    // Add click to seek functionality
                    lyricLine.addEventListener('click', () => {
                        this.mediaPlayer.currentTime = segment.start_time;
                    });
                    
                    this.lyricsDisplay.appendChild(lyricLine);
                });
            }
            
            updateLyrics() {
                const currentTime = this.mediaPlayer.currentTime;
                let newSegmentIndex = -1;
                
                // Find current segment
                for (let i = 0; i < syncData.length; i++) {
                    const segment = syncData[i];
                    if (currentTime >= segment.start_time && currentTime <= segment.end_time) {
                        newSegmentIndex = i;
                        break;
                    }
                }
                
                // Update segment highlighting
                if (newSegmentIndex !== this.currentSegmentIndex) {
                    this.updateSegmentHighlight(newSegmentIndex);
                    this.currentSegmentIndex = newSegmentIndex;
                }
                
                // Update word highlighting if we have word timings
                if (newSegmentIndex >= 0) {
                    this.updateWordHighlight(newSegmentIndex, currentTime);
                }
                
                // Update segment counter
                document.getElementById('currentSegment').textContent = 
                    newSegmentIndex >= 0 ? newSegmentIndex + 1 : '-';
            }
            
            updateSegmentHighlight(newIndex) {
                // Remove previous highlights
                document.querySelectorAll('.lyric-line').forEach((line, index) => {
                    line.classList.remove('current', 'past', 'future');
                    
                    if (index < newIndex) {
                        line.classList.add('past');
                    } else if (index === newIndex) {
                        line.classList.add('current');
                        
                        // Auto-scroll to current line
                        if (this.autoScroll) {
                            line.scrollIntoView({ 
                                behavior: 'smooth', 
                                block: 'center' 
                            });
                        }
                    } else {
                        line.classList.add('future');
                    }
                });
            }
            
            updateWordHighlight(segmentIndex, currentTime) {
                const segment = syncData[segmentIndex];
                if (!segment.word_timings || segment.word_timings.length === 0) {
                    return;
                }
                
                const line = document.getElementById(`line-${segmentIndex}`);
                let highlightedText = segment.text;
                
                // Find current word
                for (let i = 0; i < segment.word_timings.length; i++) {
                    const word = segment.word_timings[i];
                    if (currentTime >= word.start && currentTime <= word.end) {
                        // Highlight current word
                        const wordRegex = new RegExp(this.escapeRegex(word.word.trim()), 'i');
                        highlightedText = highlightedText.replace(wordRegex, 
                            `<span class="word-highlight">${word.word.trim()}</span>`);
                        break;
                    }
                }
                
                line.innerHTML = highlightedText;
            }
            
            escapeRegex(string) {
                return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
            }
            
            updateProgress() {
                if (this.mediaPlayer.duration) {
                    const progress = (this.mediaPlayer.currentTime / this.mediaPlayer.duration) * 100;
                    document.getElementById('progressFill').style.width = progress + '%';
                    document.getElementById('progressHandle').style.left = progress + '%';
                }
                
                // Update time display
                document.getElementById('currentTime').textContent = 
                    this.formatTime(this.mediaPlayer.currentTime);
            }
            
            updateDuration() {
                document.getElementById('duration').textContent = 
                    this.formatTime(this.mediaPlayer.duration);
            }
            
            formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins}:${secs.toString().padStart(2, '0')}`;
            }
            
            togglePlayPause() {
                const btn = document.getElementById('playPauseBtn');
                if (this.mediaPlayer.paused) {
                    this.mediaPlayer.play();
                    btn.textContent = '⏸️ Pause';
                } else {
                    this.mediaPlayer.pause();
                    btn.textContent = '▶️ Play';
                }
            }
            
            updateFontSize(size) {
                document.querySelectorAll('.lyric-line').forEach(line => {
                    line.style.fontSize = size + 'px';
                });
            }
            
            seekToPosition(event) {
                const progressBar = event.currentTarget;
                const rect = progressBar.getBoundingClientRect();
                const clickX = event.clientX - rect.left;
                const percentage = clickX / rect.width;
                
                if (this.mediaPlayer.duration) {
                    this.mediaPlayer.currentTime = percentage * this.mediaPlayer.duration;
                }
            }
            
            handleKeyboard(event) {
                switch(event.code) {
                    case 'Space':
                        event.preventDefault();
                        this.togglePlayPause();
                        break;
                    case 'ArrowLeft':
                        this.mediaPlayer.currentTime = Math.max(0, this.mediaPlayer.currentTime - 5);
                        break;
                    case 'ArrowRight':
                        this.mediaPlayer.currentTime = Math.min(this.mediaPlayer.duration, this.mediaPlayer.currentTime + 5);
                        break;
                }
            }
            
            displaySyncQuality() {
                const totalSegments = syncData.length;
                const highConfidence = syncData.filter(s => s.confidence >= 0.8).length;
                const avgConfidence = syncData.reduce((sum, s) => sum + s.confidence, 0) / totalSegments;
                
                const quality = avgConfidence >= 0.8 ? 'Excellent' : 
                               avgConfidence >= 0.6 ? 'Good' : 
                               avgConfidence >= 0.4 ? 'Fair' : 'Poor';
                
                document.getElementById('syncQuality').textContent = 
                    `${quality} (${Math.round(avgConfidence * 100)}% avg, ${highConfidence}/${totalSegments} high confidence)`;
            }
        }
        
        // Initialize player when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new LyricsPlayer();
        });
        """
    
    def start_local_server(self, port: int = 8080) -> str:
        """Start a local HTTP server to serve the player files."""
        os.chdir(self.output_dir)
        
        class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress log messages
        
        try:
            with socketserver.TCPServer(("", port), QuietHTTPRequestHandler) as httpd:
                server_url = f"http://localhost:{port}/lyrics_player.html"
                print(f"🌐 Starting local server at: {server_url}")
                print("🎵 Opening lyrics player in browser...")
                
                # Open browser in a separate thread
                def open_browser():
                    time.sleep(1)  # Give server time to start
                    webbrowser.open(server_url)
                
                Thread(target=open_browser, daemon=True).start()
                
                print("✅ Server running! Press Ctrl+C to stop.")
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
            return server_url
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"⚠️ Port {port} is busy, trying port {port + 1}...")
                return self.start_local_server(port + 1)
            else:
                raise

def create_lyrics_video_player(audio_path: str, 
                             sync_json_path: str,
                             video_path: Optional[str] = None,
                             output_dir: str = "./player_output",
                             title: str = "Synchronized Lyrics Player",
                             auto_open: bool = True,
                             server_port: int = 8080) -> str:
    """
    Create and optionally serve a synchronized lyrics video player.
    
    Args:
        audio_path: Path to audio file
        sync_json_path: Path to synchronized lyrics JSON
        video_path: Optional path to video file
        output_dir: Directory to save player files
        title: Title for the player
        auto_open: Whether to automatically open in browser
        server_port: Port for local server
        
    Returns:
        Path to generated HTML file or server URL
    """
    print("🎬 Creating synchronized lyrics video player...")
    
    # Validate input files
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not os.path.exists(sync_json_path):
        raise FileNotFoundError(f"Sync JSON file not found: {sync_json_path}")
    if video_path and not os.path.exists(video_path):
        print(f"⚠️ Video file not found, using audio only: {video_path}")
        video_path = None
    
    # Create player
    player = LyricsVideoPlayer(output_dir)
    html_path = player.generate_html_player(
        audio_path, sync_json_path, video_path, title
    )
    
    if auto_open:
        # Start local server and open in browser
        try:
            server_url = player.start_local_server(server_port)
            return server_url
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            print(f"📁 You can manually open: {html_path}")
            return html_path
    else:
        return html_path

def main():
    """Command-line interface for creating lyrics video player."""
    parser = argparse.ArgumentParser(
        description="Create synchronized lyrics video player from sync data"
    )
    
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("sync_json", help="Path to synchronized lyrics JSON file")
    parser.add_argument("--video_file", default=None, help="Optional path to video file")
    parser.add_argument("--output_dir", default="./player_output", 
                       help="Output directory for player files")
    parser.add_argument("--title", default="Synchronized Lyrics Player",
                       help="Title for the player")
    parser.add_argument("--no_auto_open", action="store_true",
                       help="Don't automatically open in browser")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port for local server")
    
    args = parser.parse_args()
    
    try:
        result = create_lyrics_video_player(
            audio_path=args.audio_file,
            sync_json_path=args.sync_json,
            video_path=args.video_file,
            output_dir=args.output_dir,
            title=args.title,
            auto_open=not args.no_auto_open,
            server_port=args.port
        )
        
        print(f"\n🎉 Lyrics video player created!")
        print(f"📍 Location: {result}")
        
    except Exception as e:
        print(f"❌ Error creating player: {e}")
        raise

if __name__ == "__main__":
    main()
