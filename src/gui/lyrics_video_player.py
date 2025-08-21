"""
Enhanced Karaoke Player with Professional Features
Integrates lyrics_video_player.py functionality with audio playback
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import webbrowser
import tempfile
import shutil
import subprocess
import sys
import platform

class MacOSAudioPlayer:
    """Audio player using macOS system commands - much more reliable than pygame"""
    
    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.total_length = 0
        self.process = None
        self.start_time = 0
        self.pause_position = 0
        self.audio_file = None
        self.is_initialized = True  # Always true for macOS system player
        
    def load_audio(self, file_path: str) -> bool:
        """Load audio file"""
        try:
            if not Path(file_path).exists():
                print(f"❌ File not found: {file_path}")
                return False
                
            self.audio_file = str(Path(file_path).absolute())
            
            # Get duration using afinfo (macOS built-in)
            try:
                result = subprocess.run(['afinfo', self.audio_file], 
                                     capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'estimated duration' in line:
                        duration_str = line.split(':')[1].strip().split()[0]
                        self.total_length = float(duration_str)
                        break
                else:
                    # Fallback: estimate from file size (rough)
                    file_size = Path(self.audio_file).stat().st_size
                    # Rough estimate: 44.1kHz * 16bit * 2channels = ~176KB per second
                    self.total_length = file_size / (44100 * 2 * 2)
                    
            except Exception as e:
                print(f"⚠️ Could not determine duration: {e}")
                self.total_length = 300  # 5 min default
                
            print(f"🎵 Loaded: {Path(file_path).name} ({self.total_length:.1f}s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            return False
    
    def play(self) -> bool:
        """Start playback using afplay (macOS built-in)"""
        try:
            # Stop any existing playback
            if self.process:
                self.process.terminate()
                self.process = None
            
            print(f"▶️ Starting playback: {Path(self.audio_file).name}")
            
            # Use afplay for reliable macOS audio playback
            if self.current_position > 0:
                # For seeking, we need to use a different approach
                # afplay doesn't support seeking, so we'll use ffplay if available
                try:
                    self.process = subprocess.Popen([
                        'ffplay', '-ss', str(self.current_position), 
                        '-nodisp', '-autoexit', '-loglevel', 'quiet',
                        self.audio_file
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"🎵 Using ffplay with seek to {self.current_position:.1f}s")
                except FileNotFoundError:
                    # Fallback: use afplay from beginning
                    print("⚠️ ffplay not found, playing from beginning")
                    self.current_position = 0
                    self.process = subprocess.Popen(['afplay', self.audio_file])
            else:
                # Play from beginning with afplay
                self.process = subprocess.Popen(['afplay', self.audio_file])
                print("🎵 Using afplay from beginning")
                
            self.is_playing = True
            self.is_paused = False
            self.start_time = time.time() - self.current_position
            
            # Start a thread to monitor when playback ends
            threading.Thread(target=self._monitor_playback, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ Playback failed: {e}")
            return False
    
    def _monitor_playback(self):
        """Monitor when playback ends"""
        if self.process:
            self.process.wait()  # Wait for process to end
            if self.is_playing:  # If we were supposed to be playing
                self.is_playing = False
                print("⏹️ Playback ended")
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and self.process:
            self.pause_position = self.get_position()
            self.process.terminate()
            self.process = None
            self.is_playing = False
            self.is_paused = True
            print(f"⏸️ Paused at {self.pause_position:.1f}s")
    
    def stop(self):
        """Stop playback"""
        if self.process:
            self.process.terminate()
            self.process = None
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.pause_position = 0
        print("⏹️ Stopped")
    
    def get_position(self) -> float:
        """Get current playback position"""
        if not self.is_playing and not self.is_paused:
            return self.current_position
        
        if self.is_paused:
            return self.pause_position
        
        if self.is_playing:
            elapsed = time.time() - self.start_time
            return min(elapsed, self.total_length)
        
        return self.current_position
    
    def seek(self, position: float):
        """Seek to position"""
        was_playing = self.is_playing
        self.current_position = max(0, min(position, self.total_length))
        
        if was_playing:
            self.stop()
            self.play()
        
        print(f"⏭️ Seeked to {self.current_position:.1f}s")
    
    def set_volume(self, volume: float):
        """Set system volume (macOS)"""
        try:
            vol_level = max(0, min(100, int(volume * 100)))
            subprocess.run(['osascript', '-e', f'set volume output volume {vol_level}'], 
                         capture_output=True)
        except Exception as e:
            print(f"⚠️ Volume control failed: {e}")

class AudioPlayer:
    """Smart audio player that chooses the best backend for the platform"""
    
    def __init__(self):
        self.backend = None
        self.is_initialized = False
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the best available audio backend"""
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            print("🍎 Using macOS system audio player (afplay)")
            self.backend = MacOSAudioPlayer()
            self.is_initialized = True
        else:
            # Try pygame for other systems
            try:
                import pygame
                self.backend = self._create_pygame_player()
                self.is_initialized = True
                print("🎮 Using pygame audio player")
            except ImportError:
                print("❌ No suitable audio backend found")
                self.is_initialized = False
    
    def _create_pygame_player(self):
        """Create pygame player (for non-macOS systems)"""
        import pygame
        
        class PygamePlayer:
            def __init__(self):
                pygame.mixer.init()
                self.is_initialized = True
                self.total_length = 0
                self.start_time = 0
                self.is_playing = False
                self.is_paused = False
                self.current_position = 0
                self.pause_position = 0
            
            def load_audio(self, file_path):
                try:
                    pygame.mixer.music.load(file_path)
                    # Estimate duration
                    import librosa
                    self.total_length = librosa.get_duration(filename=file_path)
                    return True
                except Exception as e:
                    print(f"❌ Failed to load: {e}")
                    return False
            
            def play(self):
                try:
                    if self.is_paused:
                        pygame.mixer.music.unpause()
                        self.start_time = time.time() - self.pause_position
                        self.is_paused = False
                    else:
                        pygame.mixer.music.play(start=self.current_position)
                        self.start_time = time.time() - self.current_position
                    self.is_playing = True
                    return True
                except Exception as e:
                    print(f"❌ Play failed: {e}")
                    return False
            
            def pause(self):
                if self.is_playing:
                    pygame.mixer.music.pause()
                    self.pause_position = self.get_position()
                    self.is_paused = True
                    self.is_playing = False
            
            def stop(self):
                pygame.mixer.music.stop()
                self.is_playing = False
                self.is_paused = False
                self.current_position = 0
                self.pause_position = 0
            
            def get_position(self):
                if not self.is_playing and not self.is_paused:
                    return self.current_position
                if self.is_paused:
                    return self.pause_position
                return time.time() - self.start_time
            
            def seek(self, position):
                self.current_position = max(0, min(position, self.total_length))
                if self.is_playing or self.is_paused:
                    self.stop()
                    self.play()
            
            def set_volume(self, volume):
                pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        
        return PygamePlayer()
    
    # Delegate all methods to the backend
    def load_audio(self, file_path: str) -> bool:
        return self.backend.load_audio(file_path) if self.backend else False
    
    def play(self) -> bool:
        return self.backend.play() if self.backend else False
    
    def pause(self):
        if self.backend:
            self.backend.pause()
    
    def stop(self):
        if self.backend:
            self.backend.stop()
    
    def get_position(self) -> float:
        return self.backend.get_position() if self.backend else 0.0
    
    def seek(self, position: float):
        if self.backend:
            self.backend.seek(position)
    
    def set_volume(self, volume: float):
        if self.backend:
            self.backend.set_volume(volume)
    
    @property
    def total_length(self) -> float:
        return self.backend.total_length if self.backend else 0.0
    
    @property
    def is_playing(self) -> bool:
        return self.backend.is_playing if self.backend else False
    
    @property
    def is_paused(self) -> bool:
        return self.backend.is_paused if self.backend else False

class EnhancedKaraokePlayer:
    """Enhanced karaoke player with professional features"""
    
    def __init__(self, instrumental_path: str, sync_json_path: str, song_name: str, 
                 launch_web_player: bool = True):
        self.instrumental_path = instrumental_path
        self.sync_json_path = sync_json_path
        self.song_name = song_name
        self.launch_web_player = launch_web_player
        
        # Load sync data
        with open(sync_json_path, 'r', encoding='utf-8') as f:
            self.sync_data = json.load(f)
        
        self.segments = self.sync_data['segments']
        self.current_segment = -1
        self.current_word = -1
        
        # Audio player
        self.audio_player = AudioPlayer()
        
        # UI state
        self.is_fullscreen = False
        self.font_size = 24
        self.auto_scroll = True
        
        # Web player
        self.web_player_url = None
        
        self.setup_player_window()
        self.load_audio()
        
        if self.launch_web_player:
            self.create_web_player()
    
    def setup_player_window(self):
        """Setup the main karaoke player window"""
        self.window = tk.Tk()
        self.window.title(f"🎤 Noraemong Karaoke - {self.song_name}")
        self.window.geometry("1200x800")
        self.window.configure(bg='#1a1a1a')
        
        # Configure styles
        self.setup_styles()
        
        # Bind keyboard shortcuts
        self.window.bind('<space>', lambda e: self.toggle_play())
        self.window.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.window.bind('<Escape>', lambda e: self.exit_fullscreen())
        self.window.bind('<Left>', lambda e: self.seek_relative(-10))
        self.window.bind('<Right>', lambda e: self.seek_relative(10))
        self.window.bind('<Up>', lambda e: self.change_font_size(2))
        self.window.bind('<Down>', lambda e: self.change_font_size(-2))
        
        # Focus window for keyboard input
        self.window.focus_set()
        
        # Create main layout
        self.create_main_layout()
        
        # Start update loop
        self.update_display()
    
    def setup_styles(self):
        """Setup custom styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles for dark theme
        self.style.configure('Dark.TFrame', background='#1a1a1a')
        self.style.configure('Dark.TLabel', background='#1a1a1a', foreground='#ffffff')
        self.style.configure('Title.TLabel', background='#1a1a1a', foreground='#3498db', 
                           font=('Arial', 20, 'bold'))
        self.style.configure('Control.TButton', font=('Arial', 10, 'bold'))
        self.style.configure('Big.TButton', font=('Arial', 14, 'bold'), padding=10)
    
    def create_main_layout(self):
        """Create the main player layout"""
        # Main container
        self.main_frame = ttk.Frame(self.window, style='Dark.TFrame', padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title section
        self.create_title_section()
        
        # Control section
        self.create_control_section()
        
        # Progress section
        self.create_progress_section()
        
        # Lyrics section
        self.create_lyrics_section()
        
        # Status section
        self.create_status_section()
    
    def create_title_section(self):
        """Create title and song info section"""
        title_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Song title
        title_label = ttk.Label(title_frame, text=f"🎤 {self.song_name}", 
                               style='Title.TLabel')
        title_label.pack()
        
        # Song info
        info_text = f"🎵 {len(self.segments)} lyrics segments"
        if self.sync_data.get('metadata'):
            avg_conf = sum(s.get('confidence', 0) for s in self.segments) / len(self.segments)
            info_text += f" • Quality: {avg_conf:.1%}"
        
        info_label = ttk.Label(title_frame, text=info_text, style='Dark.TLabel')
        info_label.pack()
    
    def create_control_section(self):
        """Create playback control section"""
        control_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Playback controls
        play_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        play_frame.pack(side=tk.LEFT)
        
        self.play_btn = ttk.Button(play_frame, text="▶️ Play", 
                                  command=self.toggle_play, style='Big.TButton')
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        stop_btn = ttk.Button(play_frame, text="⏹️ Stop", 
                             command=self.stop_playback, style='Control.TButton')
        stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        restart_btn = ttk.Button(play_frame, text="🔄 Restart", 
                               command=self.restart_playback, style='Control.TButton')
        restart_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Seek controls
        seek_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        seek_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Button(seek_frame, text="⏪ -10s", 
                  command=lambda: self.seek_relative(-10), style='Control.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seek_frame, text="⏩ +10s", 
                  command=lambda: self.seek_relative(10), style='Control.TButton').pack(side=tk.LEFT)
        
        # Volume control
        volume_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        volume_frame.pack(side=tk.RIGHT)
        
        ttk.Label(volume_frame, text="🔊", style='Dark.TLabel').pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=70)
        volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                               variable=self.volume_var, command=self.on_volume_change)
        volume_scale.pack(side=tk.LEFT, padx=(5, 0))
        
        # Display options
        options_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        options_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Button(options_frame, text="🌐 Web Player", 
                  command=self.open_web_player, style='Control.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(options_frame, text="⛶ Fullscreen", 
                  command=self.toggle_fullscreen, style='Control.TButton').pack(side=tk.LEFT)
    
    def create_progress_section(self):
        """Create progress bar section"""
        progress_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Time labels
        time_frame = ttk.Frame(progress_frame, style='Dark.TFrame')
        time_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.current_time_var = tk.StringVar(value="00:00")
        self.total_time_var = tk.StringVar(value="00:00")
        
        ttk.Label(time_frame, textvariable=self.current_time_var, 
                 style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Label(time_frame, textvariable=self.total_time_var, 
                 style='Dark.TLabel').pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Click to seek
        self.progress_bar.bind("<Button-1>", self.on_progress_click)
    
    def create_lyrics_section(self):
        """Create lyrics display section"""
        lyrics_frame = ttk.LabelFrame(self.main_frame, text="🎵 Lyrics", padding="15")
        lyrics_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Lyrics controls
        controls_frame = ttk.Frame(lyrics_frame, style='Dark.TFrame')
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-scroll toggle
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(controls_frame, text="Auto-scroll", 
                                        variable=self.auto_scroll_var,
                                        command=self.on_auto_scroll_change)
        auto_scroll_cb.pack(side=tk.LEFT)
        
        # Font size controls
        font_frame = ttk.Frame(controls_frame, style='Dark.TFrame')
        font_frame.pack(side=tk.RIGHT)
        
        ttk.Label(font_frame, text="Font:", style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Button(font_frame, text="A-", 
                  command=lambda: self.change_font_size(-2), style='Control.TButton').pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(font_frame, text="A+", 
                  command=lambda: self.change_font_size(2), style='Control.TButton').pack(side=tk.LEFT)
        
        # Lyrics display area
        self.create_lyrics_display(lyrics_frame)
    
    def create_lyrics_display(self, parent):
        """Create scrollable lyrics display"""
        # Create canvas with scrollbar
        canvas_frame = ttk.Frame(parent, style='Dark.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.lyrics_canvas = tk.Canvas(canvas_frame, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.lyrics_canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.lyrics_canvas, bg='#2c3e50')
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.lyrics_canvas.configure(scrollregion=self.lyrics_canvas.bbox("all"))
        )
        
        self.lyrics_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.lyrics_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.lyrics_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create lyrics labels
        self.lyrics_labels = []
        for i, segment in enumerate(self.segments):
            label = tk.Label(self.scrollable_frame, 
                           text=segment['text'],
                           font=('Arial', self.font_size),
                           bg='#2c3e50',
                           fg='#bdc3c7',
                           wraplength=800,
                           justify=tk.LEFT,
                           pady=15,
                           cursor='hand2')
            
            # Click to seek functionality
            label.bind("<Button-1>", lambda e, idx=i: self.seek_to_segment(idx))
            
            label.pack(fill=tk.X, padx=20, pady=5)
            self.lyrics_labels.append(label)
        
        # Mouse wheel scrolling
        self.lyrics_canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def create_status_section(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.X)
        
        # Status info
        self.status_var = tk.StringVar(value="Ready to play")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                style='Dark.TLabel')
        status_label.pack(side=tk.LEFT)
        
        # Segment counter
        self.segment_var = tk.StringVar(value=f"0 / {len(self.segments)}")
        segment_label = ttk.Label(status_frame, textvariable=self.segment_var, 
                                 style='Dark.TLabel')
        segment_label.pack(side=tk.RIGHT)
        
        # Keyboard shortcuts help
        help_text = "Shortcuts: Space=Play/Pause, ←→=Seek, ↑↓=Font, F11=Fullscreen"
        help_label = ttk.Label(status_frame, text=help_text, 
                              style='Dark.TLabel', font=('Arial', 8))
        help_label.pack()
    
    def load_audio(self):
        """Load the instrumental audio"""
        if self.audio_player.load_audio(self.instrumental_path):
            total_seconds = int(self.audio_player.total_length)
            self.total_time_var.set(f"{total_seconds//60:02d}:{total_seconds%60:02d}")
            self.status_var.set("Audio loaded successfully")
        else:
            self.status_var.set("Failed to load audio")
            messagebox.showerror("Audio Error", "Failed to load instrumental audio")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.audio_player.is_playing:
            self.audio_player.pause()
            self.play_btn.config(text="▶️ Play")
            self.status_var.set("Paused")
        else:
            if self.audio_player.play():
                self.play_btn.config(text="⏸️ Pause")
                self.status_var.set("Playing")
            else:
                messagebox.showerror("Playback Error", "Failed to start playback")
    
    def stop_playback(self):
        """Stop playback"""
        self.audio_player.stop()
        self.play_btn.config(text="▶️ Play")
        self.status_var.set("Stopped")
        self.current_segment = -1
        self.update_lyrics_display()
    
    def restart_playback(self):
        """Restart from beginning"""
        self.audio_player.stop()
        self.audio_player.current_position = 0
        self.toggle_play()
    
    def seek_relative(self, seconds: float):
        """Seek relative to current position"""
        current_pos = self.audio_player.get_position()
        new_pos = max(0, min(current_pos + seconds, self.audio_player.total_length))
        self.audio_player.seek(new_pos)
    
    def seek_to_segment(self, segment_index: int):
        """Seek to specific segment"""
        if 0 <= segment_index < len(self.segments):
            self.audio_player.seek(self.segments[segment_index]['start_time'])
    
    def on_progress_click(self, event):
        """Handle progress bar click for seeking"""
        if self.audio_player.total_length > 0:
            click_ratio = event.x / self.progress_bar.winfo_width()
            new_position = click_ratio * self.audio_player.total_length
            self.audio_player.seek(new_position)
    
    def on_volume_change(self, value):
        """Handle volume change"""
        volume = float(value) / 100.0
        self.audio_player.set_volume(volume)
    
    def on_auto_scroll_change(self):
        """Handle auto-scroll toggle"""
        self.auto_scroll = self.auto_scroll_var.get()
    
    def change_font_size(self, delta: int):
        """Change lyrics font size"""
        new_size = max(12, min(48, self.font_size + delta))
        if new_size != self.font_size:
            self.font_size = new_size
            for label in self.lyrics_labels:
                label.config(font=('Arial', self.font_size))
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.lyrics_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.window.attributes('-fullscreen', self.is_fullscreen)
        
        if self.is_fullscreen:
            self.window.configure(cursor='none')
        else:
            self.window.configure(cursor='')
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.window.attributes('-fullscreen', False)
            self.window.configure(cursor='')
    
    def update_display(self):
        """Update display elements"""
        try:
            # Update time and progress
            current_time = self.audio_player.get_position()
            current_seconds = int(current_time)
            self.current_time_var.set(f"{current_seconds//60:02d}:{current_seconds%60:02d}")
            
            if self.audio_player.total_length > 0:
                progress = (current_time / self.audio_player.total_length) * 100
                self.progress_var.set(min(progress, 100))
            
            # Update lyrics
            self.update_lyrics_display()
            
            # Schedule next update
            self.window.after(100, self.update_display)
            
        except tk.TclError:
            # Window was closed
            pass
    
    def update_lyrics_display(self):
        """Update lyrics highlighting based on current time"""
        current_time = self.audio_player.get_position()
        new_segment = -1
        
        # Find current segment
        for i, segment in enumerate(self.segments):
            if segment['start_time'] <= current_time <= segment['end_time']:
                new_segment = i
                break
        
        # Update highlighting if segment changed
        if new_segment != self.current_segment:
            # Remove previous highlighting
            if 0 <= self.current_segment < len(self.lyrics_labels):
                self.lyrics_labels[self.current_segment].config(
                    fg='#bdc3c7', bg='#2c3e50', 
                    font=('Arial', self.font_size)
                )
            
            # Highlight current segment
            if 0 <= new_segment < len(self.lyrics_labels):
                self.lyrics_labels[new_segment].config(
                    fg='#ffffff', bg='#3498db', 
                    font=('Arial', self.font_size, 'bold')
                )
                
                # Auto-scroll to current segment
                if self.auto_scroll:
                    self.scroll_to_segment(new_segment)
            
            self.current_segment = new_segment
            
            # Update segment counter
            current_num = new_segment + 1 if new_segment >= 0 else 0
            self.segment_var.set(f"{current_num} / {len(self.segments)}")
    
    def scroll_to_segment(self, segment_index: int):
        """Auto-scroll to current segment"""
        if 0 <= segment_index < len(self.lyrics_labels):
            label = self.lyrics_labels[segment_index]
            
            # Calculate scroll position
            canvas_height = self.lyrics_canvas.winfo_height()
            frame_height = self.scrollable_frame.winfo_reqheight()
            
            if frame_height > canvas_height:
                label_y = label.winfo_y()
                label_height = label.winfo_reqheight()
                
                # Calculate target position (center the current line)
                target_y = label_y + label_height / 2 - canvas_height / 2
                scroll_fraction = max(0, min(1, target_y / frame_height))
                
                self.lyrics_canvas.yview_moveto(scroll_fraction)
    
    def create_web_player(self):
        """Create web-based karaoke player using lyrics_video_player.py approach"""
        try:
            # Import the web player module
            from lyrics_video_player import create_lyrics_video_player
            
            # Create temporary directory for web player
            temp_dir = tempfile.mkdtemp(prefix="noraemong_karaoke_")
            
            # Create the web player
            self.web_player_url = create_lyrics_video_player(
                audio_path=self.instrumental_path,
                sync_json_path=self.sync_json_path,
                output_dir=temp_dir,
                title=f"🎤 {self.song_name} - Karaoke",
                auto_open=False,  # Don't auto-open, we'll handle it manually
                server_port=8080
            )
            
            print(f"🌐 Web player created: {self.web_player_url}")
            
        except Exception as e:
            print(f"❌ Failed to create web player: {e}")
            self.web_player_url = None
    
    def open_web_player(self):
        """Open web-based karaoke player"""
        if self.web_player_url:
            webbrowser.open(self.web_player_url)
        else:
            # Fallback: create simple HTML player
            self.create_simple_web_player()
    
    def create_simple_web_player(self):
        """Create a simple web player as fallback"""
        try:
            # Create temporary HTML file
            temp_dir = tempfile.mkdtemp(prefix="noraemong_simple_")
            html_file = Path(temp_dir) / "karaoke.html"
            
            # Copy audio file to temp directory
            audio_name = Path(self.instrumental_path).name
            shutil.copy2(self.instrumental_path, temp_dir / audio_name)
            
            # Create simple HTML player
            html_content = self.generate_simple_html_player(audio_name)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Open in browser
            webbrowser.open(f"file://{html_file}")
            print(f"🌐 Simple web player opened: {html_file}")
            
        except Exception as e:
            print(f"❌ Failed to create simple web player: {e}")
            messagebox.showerror("Web Player Error", f"Failed to create web player: {str(e)}")
    
    def generate_simple_html_player(self, audio_filename: str) -> str:
        """Generate simple HTML karaoke player"""
        segments_js = json.dumps(self.segments, indent=2)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 {self.song_name} - Karaoke</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: white;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .audio-player {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        audio {{
            width: 100%;
            max-width: 600px;
        }}
        
        .lyrics-display {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            min-height: 400px;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .lyric-line {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
            font-size: 24px;
            line-height: 1.5;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .lyric-line:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        .lyric-line.current {{
            background: rgba(255,255,255,0.2);
            transform: scale(1.02);
            border-left: 4px solid #4ecdc4;
            font-weight: bold;
        }}
        
        .lyric-line.past {{
            opacity: 0.6;
        }}
        
        .controls {{
            margin: 20px 0;
        }}
        
        .control-btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            margin: 0 5px;
            font-size: 16px;
        }}
        
        .control-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 {self.song_name}</h1>
        
        <div class="audio-player">
            <audio id="audioPlayer" controls>
                <source src="{audio_filename}" type="audio/mpeg">
                <source src="{audio_filename}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="toggleAutoScroll()">🔄 Auto-scroll: ON</button>
            <button class="control-btn" onclick="changeFontSize(-2)">A-</button>
            <button class="control-btn" onclick="changeFontSize(2)">A+</button>
            <button class="control-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
        </div>
        
        <div class="lyrics-display" id="lyricsDisplay">
            <!-- Lyrics will be populated by JavaScript -->
        </div>
    </div>

    <script>
        const segments = {segments_js};
        const audioPlayer = document.getElementById('audioPlayer');
        const lyricsDisplay = document.getElementById('lyricsDisplay');
        
        let currentSegment = -1;
        let autoScroll = true;
        let fontSize = 24;
        
        // Initialize lyrics display
        function initLyrics() {{
            lyricsDisplay.innerHTML = '';
            segments.forEach((segment, index) => {{
                const lyricDiv = document.createElement('div');
                lyricDiv.className = 'lyric-line';
                lyricDiv.id = `line-${{index}}`;
                lyricDiv.textContent = segment.text;
                lyricDiv.style.fontSize = fontSize + 'px';
                
                // Click to seek
                lyricDiv.addEventListener('click', () => {{
                    audioPlayer.currentTime = segment.start_time;
                }});
                
                lyricsDisplay.appendChild(lyricDiv);
            }});
        }}
        
        // Update lyrics highlighting
        function updateLyrics() {{
            const currentTime = audioPlayer.currentTime;
            let newSegment = -1;
            
            for (let i = 0; i < segments.length; i++) {{
                const segment = segments[i];
                if (currentTime >= segment.start_time && currentTime <= segment.end_time) {{
                    newSegment = i;
                    break;
                }}
            }}
            
            if (newSegment !== currentSegment) {{
                // Remove previous highlighting
                if (currentSegment >= 0) {{
                    const prevLine = document.getElementById(`line-${{currentSegment}}`);
                    if (prevLine) {{
                        prevLine.classList.remove('current');
                        prevLine.classList.add('past');
                    }}
                }}
                
                // Add current highlighting
                if (newSegment >= 0) {{
                    const currentLine = document.getElementById(`line-${{newSegment}}`);
                    if (currentLine) {{
                        currentLine.classList.add('current');
                        currentLine.classList.remove('past');
                        
                        // Auto-scroll
                        if (autoScroll) {{
                            currentLine.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    }}
                }}
                
                // Update past lines
                for (let i = 0; i < newSegment; i++) {{
                    const line = document.getElementById(`line-${{i}}`);
                    if (line) {{
                        line.classList.add('past');
                        line.classList.remove('current');
                    }}
                }}
                
                // Update future lines
                for (let i = newSegment + 1; i < segments.length; i++) {{
                    const line = document.getElementById(`line-${{i}}`);
                    if (line) {{
                        line.classList.remove('current', 'past');
                    }}
                }}
                
                currentSegment = newSegment;
            }}
        }}
        
        // Control functions
        function toggleAutoScroll() {{
            autoScroll = !autoScroll;
            const btn = event.target;
            btn.textContent = `🔄 Auto-scroll: ${{autoScroll ? 'ON' : 'OFF'}}`;
        }}
        
        function changeFontSize(delta) {{
            fontSize = Math.max(16, Math.min(48, fontSize + delta));
            const lines = document.querySelectorAll('.lyric-line');
            lines.forEach(line => {{
                line.style.fontSize = fontSize + 'px';
            }});
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        // Event listeners
        audioPlayer.addEventListener('timeupdate', updateLyrics);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            switch(e.code) {{
                case 'Space':
                    e.preventDefault();
                    if (audioPlayer.paused) {{
                        audioPlayer.play();
                    }} else {{
                        audioPlayer.pause();
                    }}
                    break;
                case 'ArrowLeft':
                    audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
                    break;
                case 'ArrowRight':
                    audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 10);
                    break;
                case 'F11':
                    e.preventDefault();
                    toggleFullscreen();
                    break;
            }}
        }});
        
        // Initialize
        initLyrics();
    </script>
</body>
</html>"""
    
    def show(self):
        """Show the karaoke player window"""
        self.window.mainloop()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.audio_player.stop()
            pygame.mixer.quit()
            
            # Clean up temporary audio file if exists
            if hasattr(self.audio_player, 'temp_audio_file'):
                try:
                    import os
                    os.unlink(self.audio_player.temp_audio_file)
                except:
                    pass
        except:
            pass

# Integration function for the main GUI
def launch_enhanced_karaoke_player(instrumental_path: str, sync_json_path: str, song_name: str):
    """Launch the enhanced karaoke player"""
    try:
        # Try to import pygame
        import pygame
        
        # Create and show player
        player = EnhancedKaraokePlayer(
            instrumental_path=instrumental_path,
            sync_json_path=sync_json_path,
            song_name=song_name,
            launch_web_player=True
        )
        
        # Setup cleanup on window close
        def on_closing():
            player.cleanup()
            player.window.destroy()
        
        player.window.protocol("WM_DELETE_WINDOW", on_closing)
        player.show()
        
    except ImportError:
        # Fallback if pygame not available
        print("⚠️ pygame not available, launching basic player...")
        from karaoke_player import KaraokePlayer
        player = KaraokePlayer(instrumental_path, sync_json_path, song_name)
        player.show()
    except Exception as e:
        raise Exception(f"Failed to launch karaoke player: {str(e)}")

def main():
    """Test the enhanced karaoke player"""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python karaoke_player.py <instrumental.wav> <sync.json> <song_name>")
        return
    
    instrumental_path = sys.argv[1]
    sync_json_path = sys.argv[2]
    song_name = sys.argv[3]
    
    launch_enhanced_karaoke_player(instrumental_path, sync_json_path, song_name)

if __name__ == "__main__":
    main()