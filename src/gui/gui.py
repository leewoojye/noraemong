"""
Noraemong Karaoke Machine GUI
Main interface for creating and playing karaoke tracks with synchronized lyrics.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import json
import subprocess
import time
from typing import Optional, Dict, Any

# Add src directories to path for imports
current_dir = Path(__file__).parent  # This is src/GUI/
src_dir = current_dir.parent  # This goes to src/
root_dir = src_dir.parent  # This goes to noraemong/
audio_dir = src_dir / "audio"
lyrics_dir = src_dir / "lyrics"
sync_dir = src_dir / "sync"

sys.path.extend([str(src_dir), str(audio_dir), str(lyrics_dir), str(sync_dir)])

# Import your modules
try:
    from seperate import KaraokeSeparator
    from transcribe_vocal import AudioTranscriber
    from sync_lyrics import sync_lyrics_to_audio
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Make sure all modules are in the correct directories")

class KaraokeGUI:
    """Main GUI for the Noraemong Karaoke Machine"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎤 Noraemong Karaoke Machine")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Variables
        self.audio_file = tk.StringVar()
        self.lyrics_file = tk.StringVar()
        self.processing_mode = tk.StringVar(value="auto")
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to process audio")
        
        # Data directories
        self.data_dir = root_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "separate").mkdir(exist_ok=True)
        (self.data_dir / "transcribe_vocal").mkdir(exist_ok=True)
        (self.data_dir / "sync_output").mkdir(exist_ok=True)
        
        # Processing results
        self.separated_files = {}
        self.sync_data = {}
        
        self.create_widgets()
        
    def configure_styles(self):
        """Configure custom styles for the GUI"""
        self.style.configure('Title.TLabel', 
                           font=('Arial', 16, 'bold'),
                           background='#2c3e50',
                           foreground='#ecf0f1')
        
        self.style.configure('Subtitle.TLabel',
                           font=('Arial', 12, 'bold'),
                           background='#2c3e50', 
                           foreground='#3498db')
        
        self.style.configure('Custom.TButton',
                           font=('Arial', 10, 'bold'),
                           padding=10)
        
        self.style.configure('Success.TLabel',
                           font=('Arial', 10),
                           background='#2c3e50',
                           foreground='#27ae60')
        
        self.style.configure('Error.TLabel',
                           font=('Arial', 10),
                           background='#2c3e50',
                           foreground='#e74c3c')
    
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎤 Noraemong Karaoke Machine", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Step 1: Audio File Selection
        self.create_file_selection_section(main_frame)
        
        # Step 2: Lyrics Processing Mode
        self.create_lyrics_mode_section(main_frame)
        
        # Step 3: Processing Controls
        self.create_processing_section(main_frame)
        
        # Step 4: Results and Karaoke Player
        self.create_results_section(main_frame)
        
        # Status and Progress
        self.create_status_section(main_frame)
    
    def create_file_selection_section(self, parent):
        """Create audio file selection section"""
        section_frame = ttk.LabelFrame(parent, text="Step 1: Select Audio File", padding="15")
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Audio file selection
        audio_frame = ttk.Frame(section_frame)
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(audio_frame, text="Audio File:").pack(side=tk.LEFT)
        
        audio_entry = ttk.Entry(audio_frame, textvariable=self.audio_file, width=50)
        audio_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(audio_frame, text="Browse", 
                               command=self.browse_audio_file,
                               style='Custom.TButton')
        browse_btn.pack(side=tk.RIGHT)
        
        # Supported formats info
        info_label = ttk.Label(section_frame, 
                              text="Supported formats: MP3, WAV, FLAC, M4A",
                              font=('Arial', 9),
                              foreground='#7f8c8d')
        info_label.pack(anchor=tk.W)
    
    def create_lyrics_mode_section(self, parent):
        """Create lyrics processing mode selection"""
        section_frame = ttk.LabelFrame(parent, text="Step 2: Lyrics Processing Mode", padding="15")
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Mode selection
        mode_frame = ttk.Frame(section_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-generate mode
        auto_radio = ttk.Radiobutton(mode_frame, 
                                    text="🤖 Auto-generate lyrics from vocal track (AI transcription)",
                                    variable=self.processing_mode,
                                    value="auto",
                                    command=self.on_mode_change)
        auto_radio.pack(anchor=tk.W, pady=(0, 10))
        
        # Manual lyrics mode
        manual_radio = ttk.Radiobutton(mode_frame,
                                      text="📝 Use custom lyrics file (more accurate)",
                                      variable=self.processing_mode,
                                      value="manual",
                                      command=self.on_mode_change)
        manual_radio.pack(anchor=tk.W, pady=(0, 10))
        
        # Lyrics file selection (initially hidden)
        self.lyrics_frame = ttk.Frame(section_frame)
        
        ttk.Label(self.lyrics_frame, text="Lyrics File:").pack(side=tk.LEFT)
        
        lyrics_entry = ttk.Entry(self.lyrics_frame, textvariable=self.lyrics_file, width=50)
        lyrics_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        lyrics_browse_btn = ttk.Button(self.lyrics_frame, text="Browse",
                                      command=self.browse_lyrics_file,
                                      style='Custom.TButton')
        lyrics_browse_btn.pack(side=tk.RIGHT)
        
        # Mode descriptions
        desc_frame = ttk.Frame(section_frame)
        desc_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.auto_desc = ttk.Label(desc_frame,
                                  text="• AI will extract vocals and generate lyrics automatically\n"
                                       "• May have some transcription errors\n"
                                       "• No additional files needed",
                                  font=('Arial', 9),
                                  foreground='#27ae60')
        
        self.manual_desc = ttk.Label(desc_frame,
                                    text="• Use your own lyrics file (.txt, .lrc, .srt)\n"
                                         "• More accurate lyrics timing\n"
                                         "• Better for professional karaoke",
                                    font=('Arial', 9),
                                    foreground='#3498db')
        
        self.on_mode_change()  # Initialize display
    
    def create_processing_section(self, parent):
        """Create processing controls section"""
        section_frame = ttk.LabelFrame(parent, text="Step 3: Processing", padding="15")
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        controls_frame = ttk.Frame(section_frame)
        controls_frame.pack(fill=tk.X)
        
        # Processing settings
        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(settings_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.quality_var = tk.StringVar(value="high")
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var,
                                    values=["fast", "medium", "high"], width=10, state="readonly")
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Device:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.device_var = tk.StringVar(value="auto")
        device_combo = ttk.Combobox(settings_frame, textvariable=self.device_var,
                                   values=["auto", "cpu", "cuda"], width=10, state="readonly")
        device_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Process button
        self.process_btn = ttk.Button(controls_frame, text="🚀 Start Processing",
                                     command=self.start_processing,
                                     style='Custom.TButton')
        self.process_btn.pack(side=tk.RIGHT, padx=(20, 0))
    
    def create_results_section(self, parent):
        """Create results and karaoke player section"""
        section_frame = ttk.LabelFrame(parent, text="Step 4: Results & Karaoke Player", padding="15")
        section_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Results display
        self.results_text = tk.Text(section_frame, height=8, width=80, 
                                   bg='#34495e', fg='#ecf0f1', font=('Courier', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Karaoke player button
        player_frame = ttk.Frame(section_frame)
        player_frame.pack(fill=tk.X)
        
        self.play_karaoke_btn = ttk.Button(player_frame, text="🎤 Launch Karaoke Player",
                                          command=self.launch_karaoke_player,
                                          style='Custom.TButton',
                                          state='disabled')
        self.play_karaoke_btn.pack(side=tk.LEFT)
        
        self.open_folder_btn = ttk.Button(player_frame, text="📂 Open Output Folder",
                                         command=self.open_output_folder,
                                         style='Custom.TButton',
                                         state='disabled')
        self.open_folder_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_status_section(self, parent):
        """Create status and progress section"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                           maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT)
    
    def browse_audio_file(self):
        """Browse for audio file"""
        file_types = [
            ("Audio files", "*.mp3 *.wav *.flac *.m4a"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("FLAC files", "*.flac"),
            ("M4A files", "*.m4a"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=file_types
        )
        
        if filename:
            self.audio_file.set(filename)
    
    def browse_lyrics_file(self):
        """Browse for lyrics file"""
        file_types = [
            ("Text files", "*.txt *.lrc *.srt"),
            ("Plain text", "*.txt"),
            ("LRC files", "*.lrc"),
            ("SRT files", "*.srt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Lyrics File",
            filetypes=file_types
        )
        
        if filename:
            self.lyrics_file.set(filename)
    
    def on_mode_change(self):
        """Handle mode change between auto and manual"""
        if self.processing_mode.get() == "auto":
            self.lyrics_frame.pack_forget()
            self.manual_desc.pack_forget()
            self.auto_desc.pack(fill=tk.X)
        else:
            self.auto_desc.pack_forget()
            self.lyrics_frame.pack(fill=tk.X, pady=(0, 10))
            self.manual_desc.pack(fill=tk.X)
    
    def update_results(self, message: str, color: str = "#ecf0f1"):
        """Update results text area"""
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.root.update()
    
    def update_progress(self, value: float, status: str):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update()
    
    def validate_inputs(self) -> bool:
        """Validate user inputs"""
        if not self.audio_file.get():
            messagebox.showerror("Error", "Please select an audio file")
            return False
        
        if not os.path.exists(self.audio_file.get()):
            messagebox.showerror("Error", "Audio file does not exist")
            return False
        
        if self.processing_mode.get() == "manual":
            if not self.lyrics_file.get():
                messagebox.showerror("Error", "Please select a lyrics file for manual mode")
                return False
            
            if not os.path.exists(self.lyrics_file.get()):
                messagebox.showerror("Error", "Lyrics file does not exist")
                return False
        
        return True
    
    def start_processing(self):
        """Start the karaoke processing in a separate thread"""
        if not self.validate_inputs():
            return
        
        # Disable process button
        self.process_btn.config(state='disabled')
        self.play_karaoke_btn.config(state='disabled')
        self.open_folder_btn.config(state='disabled')
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        
        # Start processing thread
        thread = threading.Thread(target=self.process_karaoke, daemon=True)
        thread.start()
    
    def process_karaoke(self):
        """Main processing function (runs in separate thread)"""
        try:
            audio_path = self.audio_file.get()
            song_name = Path(audio_path).stem
            
            self.update_progress(0, "Starting processing...")
            self.update_results("🎵 Starting karaoke processing...")
            self.update_results(f"📁 Song: {song_name}")
            self.update_results(f"🎶 Audio: {audio_path}")
            
            # Step 1: Separate audio
            self.update_progress(10, "Separating vocals and instrumental...")
            self.update_results("\n🔄 Step 1: Separating vocals and instrumental...")
            
            separator = KaraokeSeparator(
                output_dir=str(self.data_dir / "separate"),
                quality=self.quality_var.get(),
                device=self.device_var.get(),
                enhance_vocals=True
            )
            
            self.separated_files = separator.process_song(audio_path, song_name)
            
            self.update_progress(40, "Audio separation complete")
            self.update_results("✅ Audio separation complete!")
            self.update_results(f"🎤 Vocal track: {self.separated_files['vocals']}")
            self.update_results(f"🎹 Instrumental: {self.separated_files['karaoke']}")
            
            # Step 2: Generate or sync lyrics
            if self.processing_mode.get() == "auto":
                self.update_progress(50, "Transcribing vocals to generate lyrics...")
                self.update_results("\n🔄 Step 2: Auto-generating lyrics from vocals...")
                
                # Use transcribe_vocal.py approach
                transcriber = AudioTranscriber(model_size="large-v3", device=self.device_var.get())
                segments = transcriber.transcribe_with_timestamps(self.separated_files['vocals'])
                
                # Save transcribed lyrics as txt file
                lyrics_file = self.data_dir / "transcribe_vocal" / f"{song_name}_lyrics.txt"
                with open(lyrics_file, 'w', encoding='utf-8') as f:
                    for segment in segments:
                        f.write(segment.text.strip() + "\n")
                
                self.update_results(f"📝 Generated lyrics: {lyrics_file}")
                
            else:
                lyrics_file = self.lyrics_file.get()
                self.update_results(f"\n📝 Using custom lyrics: {lyrics_file}")
            
            # Step 3: Sync lyrics with audio
            self.update_progress(70, "Synchronizing lyrics with audio...")
            self.update_results("\n🔄 Step 3: Synchronizing lyrics with audio...")
            
            sync_output_dir = str(self.data_dir / "sync_output")
            sync_files = sync_lyrics_to_audio(
                audio_path=audio_path,
                lyrics_path=str(lyrics_file),
                output_dir=sync_output_dir,
                model_size="base",  # Use lighter model for sync
                device=self.device_var.get(),
                similarity_threshold=0.6
            )
            
            self.sync_data = {
                'json_file': sync_files['json'],
                'lrc_file': sync_files['lrc'],
                'srt_file': sync_files['srt'],
                'instrumental': self.separated_files['karaoke'],
                'vocals': self.separated_files['vocals'],
                'song_name': song_name
            }
            
            self.update_progress(100, "Processing complete!")
            self.update_results("✅ Lyrics synchronization complete!")
            self.update_results(f"📊 Sync data: {sync_files['json']}")
            self.update_results(f"🎵 LRC file: {sync_files['lrc']}")
            self.update_results(f"🎬 SRT file: {sync_files['srt']}")
            
            self.update_results("\n🎉 Karaoke processing complete!")
            self.update_results("🎤 Ready to launch karaoke player!")
            
            # Enable karaoke player button
            self.play_karaoke_btn.config(state='normal')
            self.open_folder_btn.config(state='normal')
            
        except Exception as e:
            self.update_progress(0, "Processing failed")
            self.update_results(f"\n❌ Error: {str(e)}")
            messagebox.showerror("Processing Error", f"An error occurred: {str(e)}")
        
        finally:
            # Re-enable process button
            self.process_btn.config(state='normal')
    
    def test_audio_playback(self):
        """Test audio playback using system player"""
        if not self.sync_data:
            messagebox.showerror("Error", "No audio files available to test")
            return
        
        try:
            instrumental_path = self.sync_data['instrumental']
            
            # Test playback using macOS system player
            import subprocess
            import platform
            
            self.update_results("🔊 Testing audio playback...")
            
            if platform.system() == "Darwin":  # macOS
                # Use afplay for testing
                process = subprocess.Popen(['afplay', instrumental_path])
                
                # Let it play for 10 seconds
                import threading
                def stop_test():
                    import time
                    time.sleep(10)
                    process.terminate()
                    self.update_results("⏹️ Audio test completed (10 seconds)")
                
                threading.Thread(target=stop_test, daemon=True).start()
                self.update_results("✅ Audio test started - playing 10 seconds...")
                self.update_results("If you hear music, audio system is working!")
                
            else:
                # For other systems, try to find a player
                players = ['ffplay', 'mpv', 'vlc']
                for player in players:
                    try:
                        subprocess.run([player, '--version'], capture_output=True, timeout=2)
                        process = subprocess.Popen([player, instrumental_path])
                        self.update_results(f"✅ Audio test started with {player}")
                        break
                    except:
                        continue
                else:
                    # Fallback: just try to open with system default
                    import webbrowser
                    webbrowser.open(instrumental_path)
                    self.update_results("🎵 Opened audio file with system default player")
                    
        except Exception as e:
            self.update_results(f"❌ Audio test failed: {e}")
            messagebox.showerror("Audio Test Error", f"Failed to test audio: {str(e)}")
    
    def launch_karaoke_player(self):
        """Launch the web-based karaoke player (most reliable approach)"""
        if not self.sync_data:
            messagebox.showerror("Error", "No sync data available. Please process audio first.")
            return
        
        try:
            self.update_results("🌐 Launching web-based karaoke player...")
            
            # Always use web player for reliability
            self.launch_web_karaoke_player()
            
        except Exception as e:
            messagebox.showerror("Player Error", f"Failed to launch karaoke player: {str(e)}")
    
    def launch_web_karaoke_player(self):
        """Launch web-based karaoke player - most reliable approach"""
        try:
            # Check if we have the web player module
            import sys
            sys.path.append(str(src_dir))
            
            # Import and use the lyrics_video_player
            from lyrics_video_player import create_lyrics_video_player
            
            self.update_results("🔄 Creating web karaoke player...")
            
            # Create web player with your processed files
            server_url = create_lyrics_video_player(
                audio_path=self.sync_data['instrumental'],
                sync_json_path=self.sync_data['json_file'],
                title=f"🎤 {self.sync_data['song_name']} - Noraemong Karaoke",
                auto_open=True,  # Automatically open in browser
                server_port=8080
            )
            
            self.update_results("✅ Web karaoke player launched successfully!")
            self.update_results(f"🌐 Server running at: {server_url}")
            self.update_results("🎤 Enjoy your karaoke session!")
            self.update_results("")
            self.update_results("💡 Pro tips:")
            self.update_results("   • Use Space bar to play/pause")
            self.update_results("   • Click lyrics to jump to that part")
            self.update_results("   • Use ← → arrows to seek")
            self.update_results("   • Press F11 for fullscreen karaoke")
            
        except ImportError as e:
            self.update_results("❌ Web player module not found")
            # Fallback: Create simple web player
            self.create_simple_web_karaoke()
            
        except Exception as e:
            self.update_results(f"❌ Web player failed: {e}")
            # Final fallback: Manual instructions
            self.show_manual_karaoke_instructions()
    
    def create_simple_web_karaoke(self):
        """Create a simple web karaoke player as fallback"""
        try:
            import tempfile
            import webbrowser
            import shutil
            import json
            
            self.update_results("🔄 Creating simple web karaoke player...")
            
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="noraemong_karaoke_"))
            
            # Copy audio file
            audio_name = Path(self.sync_data['instrumental']).name
            shutil.copy2(self.sync_data['instrumental'], temp_dir / audio_name)
            
            # Load and copy sync data
            with open(self.sync_data['json_file'], 'r', encoding='utf-8') as f:
                sync_data = json.load(f)
            
            # Create HTML karaoke player
            html_content = self.generate_web_karaoke_html(audio_name, sync_data)
            
            html_file = temp_dir / "karaoke.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Open in browser
            webbrowser.open(f"file://{html_file}")
            
            self.update_results("✅ Simple web karaoke player created!")
            self.update_results(f"📁 Files saved to: {temp_dir}")
            self.update_results("🌐 Karaoke player opened in your browser")
            
        except Exception as e:
            self.update_results(f"❌ Simple web player failed: {e}")
            self.show_manual_karaoke_instructions()
    
    def generate_web_karaoke_html(self, audio_filename: str, sync_data: dict) -> str:
        """Generate HTML for web karaoke player"""
        segments = sync_data.get('segments', [])
        song_name = self.sync_data['song_name']
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 {song_name} - Noraemong Karaoke</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: white;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
        }}
        
        h1 {{
            font-size: 3em;
            margin-bottom: 30px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .audio-player {{
            background: rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        audio {{
            width: 100%;
            max-width: 800px;
            height: 60px;
            border-radius: 30px;
        }}
        
        .controls {{
            margin: 20px 0;
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .control-btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 15px 25px;
            border-radius: 30px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .control-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        .lyrics-display {{
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 40px;
            min-height: 500px;
            max-height: 600px;
            overflow-y: auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        .lyric-line {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 15px;
            font-size: 28px;
            line-height: 1.6;
            transition: all 0.4s ease;
            cursor: pointer;
            opacity: 0.7;
        }}
        
        .lyric-line:hover {{
            background: rgba(255,255,255,0.15);
            transform: scale(1.02);
        }}
        
        .lyric-line.current {{
            background: linear-gradient(45deg, rgba(255,107,107,0.3), rgba(78,205,196,0.3));
            transform: scale(1.05);
            border-left: 6px solid #4ecdc4;
            font-weight: bold;
            opacity: 1;
            box-shadow: 0 5px 20px rgba(78,205,196,0.3);
        }}
        
        .lyric-line.past {{
            opacity: 0.5;
        }}
        
        .current-word {{
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            padding: 2px 6px;
            border-radius: 6px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: wordPulse 0.3s ease-in-out;
            box-shadow: 0 2px 10px rgba(255,107,107,0.4);
        }}
        
        .past-word {{
            color: #bdc3c7;
            opacity: 0.7;
        }}
        
        .next-word {{
            background: rgba(255,255,255,0.2);
            padding: 1px 4px;
            border-radius: 4px;
            border: 1px dashed rgba(255,255,255,0.5);
        }}
        
        @keyframes wordPulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); }}
        }}
        
        .info-bar {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        
        .progress-info {{
            font-size: 18px;
            font-weight: bold;
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2em; }}
            .lyric-line {{ font-size: 24px; padding: 15px; }}
            .controls {{ flex-direction: column; align-items: center; }}
            .info-bar {{ flex-direction: column; text-align: center; gap: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 {song_name}</h1>
        
        <div class="audio-player">
            <audio id="audioPlayer" controls autoplay>
                <source src="{audio_filename}" type="audio/mpeg">
                <source src="{audio_filename}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="toggleAutoScroll()">🔄 Auto-scroll: ON</button>
            <button class="control-btn" onclick="changeFontSize(-4)">A-</button>
            <button class="control-btn" onclick="changeFontSize(4)">A+</button>
            <button class="control-btn" onclick="toggleWordHighlight()">✨ Word Highlight: ON</button>
            <button class="control-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
            <button class="control-btn" onclick="restartSong()">🔄 Restart</button>
        </div>
        
        <div class="lyrics-display" id="lyricsDisplay">
            <!-- Lyrics will be populated by JavaScript -->
        </div>
        
        <div class="info-bar">
            <div class="progress-info" id="progressInfo">Ready to sing! 🎤</div>
            <div class="progress-info" id="segmentInfo">0 / {len(segments)} lines</div>
        </div>
    </div>

    <script>
        const segments = {json.dumps(segments, indent=2)};
        const audioPlayer = document.getElementById('audioPlayer');
        const lyricsDisplay = document.getElementById('lyricsDisplay');
        const progressInfo = document.getElementById('progressInfo');
        const segmentInfo = document.getElementById('segmentInfo');
        
        let currentSegment = -1;
        let autoScroll = true;
        let fontSize = 28;
        let wordHighlight = true;
        
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
            const duration = audioPlayer.duration || 1;
            let newSegment = -1;
            
            // Simple sequential search: find the segment that contains current time
            for (let i = 0; i < segments.length; i++) {{
                const segment = segments[i];
                if (currentTime >= segment.start_time && currentTime <= segment.end_time) {{
                    newSegment = i;
                    break;
                }}
            }}
            
            // If no exact match found, find the closest upcoming segment
            // This handles gaps between segments
            if (newSegment === -1) {{
                for (let i = 0; i < segments.length; i++) {{
                    if (currentTime < segments[i].start_time) {{
                        // We're before this segment starts
                        newSegment = Math.max(0, i - 1); // Use previous segment or first segment
                        break;
                    }}
                }}
                // If we're past all segments, use the last one
                if (newSegment === -1 && segments.length > 0) {{
                    newSegment = segments.length - 1;
                }}
            }}
            
            // Only update if segment actually changed
            if (newSegment !== currentSegment && newSegment >= 0) {{
                console.log(`Moving from segment ${{currentSegment}} to ${{newSegment}} at time ${{currentTime.toFixed(2)}}s`);
                updateSegmentHighlighting(newSegment);
                currentSegment = newSegment;
            }}
            
            // Update word-level highlighting within current segment
            if (currentSegment >= 0 && wordHighlight) {{
                updateWordHighlighting(currentSegment, currentTime);
            }}
            
            // Update progress info
            const minutes = Math.floor(currentTime / 60);
            const seconds = Math.floor(currentTime % 60);
            const totalMinutes = Math.floor(duration / 60);
            const totalSeconds = Math.floor(duration % 60);
            
            progressInfo.textContent = `${{minutes}}:${{seconds.toString().padStart(2, '0')}} / ${{totalMinutes}}:${{totalSeconds.toString().padStart(2, '0')}}`;
            segmentInfo.textContent = `${{newSegment >= 0 ? newSegment + 1 : 0}} / ${{segments.length}} lines`;
        }}
        
        function updateSegmentHighlighting(newSegment) {{
            console.log(`Highlighting segment ${{newSegment}}: "${{segments[newSegment]?.text?.substring(0, 30)}}..."`);
            
            // Remove ALL highlighting and reset to original text
            for (let i = 0; i < segments.length; i++) {{
                const line = document.getElementById(`line-${{i}}`);
                if (line) {{
                    line.classList.remove('current', 'past');
                    line.innerHTML = segments[i].text; // Reset to original text
                }}
            }}
            
            // Mark all previous segments as past
            for (let i = 0; i < newSegment; i++) {{
                const line = document.getElementById(`line-${{i}}`);
                if (line) {{
                    line.classList.add('past');
                }}
            }}
            
            // Highlight current segment
            if (newSegment >= 0) {{
                const currentLine = document.getElementById(`line-${{newSegment}}`);
                if (currentLine) {{
                    currentLine.classList.add('current');
                    
                    // Auto-scroll to current line
                    if (autoScroll) {{
                        currentLine.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                }}
            }}
        }}
        
        function updateWordHighlighting(segmentIndex, currentTime) {{
            const segment = segments[segmentIndex];
            const line = document.getElementById(`line-${{segmentIndex}}`);
            
            if (!segment || !line) return;
            
            // Check if this segment has word-level timing data
            if (!segment.word_timings || segment.word_timings.length === 0) {{
                // No word timings available, just show the whole line
                line.innerHTML = segment.text;
                return;
            }}
            
            // Build highlighted text with word-level timing
            let highlightedText = segment.text;
            let activeWordFound = false;
            
            // Sort word timings by start time to ensure proper order
            const sortedWords = [...segment.word_timings].sort((a, b) => a.start - b.start);
            
            // Create a mapping of word positions in the text
            let textPosition = 0;
            const wordPositions = [];
            
            for (const wordTiming of sortedWords) {{
                const word = wordTiming.word.trim();
                const wordIndex = segment.text.toLowerCase().indexOf(word.toLowerCase(), textPosition);
                
                if (wordIndex >= 0) {{
                    wordPositions.push({{
                        timing: wordTiming,
                        start: wordIndex,
                        end: wordIndex + word.length,
                        word: segment.text.substring(wordIndex, wordIndex + word.length)
                    }});
                    textPosition = wordIndex + word.length;
                }}
            }}
            
            // Apply highlighting based on current time
            if (wordPositions.length > 0) {{
                let result = '';
                let lastPos = 0;
                
                for (const pos of wordPositions) {{
                    // Add text before this word
                    if (pos.start > lastPos) {{
                        result += segment.text.substring(lastPos, pos.start);
                    }}
                    
                    // Determine word state
                    const isCurrentWord = currentTime >= pos.timing.start && currentTime <= pos.timing.end;
                    const isPastWord = currentTime > pos.timing.end;
                    
                    if (isCurrentWord) {{
                        result += `<span class="current-word">${{pos.word}}</span>`;
                        activeWordFound = true;
                    }} else if (isPastWord) {{
                        result += `<span class="past-word">${{pos.word}}</span>`;
                    }} else {{
                        // Future word - show with subtle highlight if it's the very next word
                        const isNextWord = !activeWordFound && pos.timing.start > currentTime && 
                                         wordPositions.indexOf(pos) === wordPositions.findIndex(w => w.timing.start > currentTime);
                        if (isNextWord) {{
                            result += `<span class="next-word">${{pos.word}}</span>`;
                        }} else {{
                            result += pos.word;
                        }}
                    }}
                    
                    lastPos = pos.end;
                }}
                
                // Add any remaining text
                if (lastPos < segment.text.length) {{
                    result += segment.text.substring(lastPos);
                }}
                
                line.innerHTML = result;
            }} else {{
                // Fallback if word positioning fails
                line.innerHTML = segment.text;
            }}
        }}
        
        // Control functions
        function toggleAutoScroll() {{
            autoScroll = !autoScroll;
            event.target.textContent = `🔄 Auto-scroll: ${{autoScroll ? 'ON' : 'OFF'}}`;
        }}
        
        function toggleWordHighlight() {{
            wordHighlight = !wordHighlight;
            event.target.textContent = `✨ Word Highlight: ${{wordHighlight ? 'ON' : 'OFF'}}`;
            
            // Refresh current segment display
            if (currentSegment >= 0) {{
                if (wordHighlight) {{
                    updateWordHighlighting(currentSegment, audioPlayer.currentTime);
                }} else {{
                    // Show plain text
                    const line = document.getElementById(`line-${{currentSegment}}`);
                    if (line && segments[currentSegment]) {{
                        line.innerHTML = segments[currentSegment].text;
                    }}
                }}
            }}
        }}
        
        function changeFontSize(delta) {{
            fontSize = Math.max(20, Math.min(48, fontSize + delta));
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
        
        function restartSong() {{
            audioPlayer.currentTime = 0;
            audioPlayer.play();
        }}
        
        // Event listeners
        audioPlayer.addEventListener('timeupdate', updateLyrics);
        audioPlayer.addEventListener('loadedmetadata', initLyrics);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            switch(e.code) {{
                case 'Space':
                    if (e.target.tagName !== 'BUTTON') {{
                        e.preventDefault();
                        if (audioPlayer.paused) {{
                            audioPlayer.play();
                        }} else {{
                            audioPlayer.pause();
                        }}
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
                case 'KeyR':
                    if (e.ctrlKey || e.metaKey) {{
                        e.preventDefault();
                        restartSong();
                    }}
                    break;
            }}
        }});
        
        // Initialize when page loads
        if (audioPlayer.readyState >= 2) {{
            initLyrics();
        }}
        
        // Debug: Log segment data on load
        console.log('Loaded segments:', segments.length);
        if (segments.length > 0) {{
            console.log('First segment:', segments[0]);
            console.log('Last segment:', segments[segments.length - 1]);
            
            // Verify segments are sorted by start_time
            for (let i = 1; i < segments.length; i++) {{
                if (segments[i].start_time < segments[i-1].start_time) {{
                    console.warn(`Segments not in order! Segment ${{i}} starts before segment ${{i-1}}`);
                }}
            }}
        }}
        
        // Welcome message
        setTimeout(() => {{
            if (segments.length > 0) {{
                progressInfo.textContent = '🎤 Ready to sing! Press space to play/pause';
                // Start with first segment ready
                currentSegment = -1; // Will be set properly when audio starts
            }}
        }}, 1000);
    </script>
</body>
</html>"""
        return html
    
    def show_manual_karaoke_instructions(self):
        """Show manual instructions for karaoke"""
        self.update_results("📋 Manual Karaoke Instructions:")
        self.update_results("=" * 50)
        self.update_results("🎵 Audio file (play in any media player):")
        self.update_results(f"   {self.sync_data['instrumental']}")
        self.update_results("")
        self.update_results("📜 Lyrics files:")
        self.update_results(f"   LRC: {self.sync_data['lrc_file']}")
        self.update_results(f"   SRT: {self.sync_data['srt_file']}")
        self.update_results(f"   JSON: {self.sync_data['json_file']}")
        self.update_results("")
        self.update_results("💡 You can:")
        self.update_results("   • Play the audio file in any media player")
        self.update_results("   • Open LRC file in karaoke software")
        self.update_results("   • Use SRT file as subtitles")
        self.update_results("   • Import JSON into custom karaoke apps")

    
    def open_output_folder(self):
        """Open the output folder"""
        try:
            if sys.platform == "win32":
                os.startfile(str(self.data_dir))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.data_dir)])
            else:
                subprocess.run(["xdg-open", str(self.data_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

class KaraokePlayer:
    """Karaoke player window with synchronized lyrics"""
    
    def __init__(self, instrumental_path: str, sync_json_path: str, song_name: str):
        self.instrumental_path = instrumental_path
        self.sync_json_path = sync_json_path
        self.song_name = song_name
        
        # Load sync data
        with open(sync_json_path, 'r', encoding='utf-8') as f:
            self.sync_data = json.load(f)
        
        self.segments = self.sync_data['segments']
        self.current_segment = -1
        self.current_word = -1
        self.is_playing = False
        self.start_time = 0
        self.current_time = 0
        
        self.setup_player_window()
    
    def setup_player_window(self):
        """Setup the karaoke player window"""
        self.player_window = tk.Toplevel()
        self.player_window.title(f"🎤 Karaoke Player - {self.song_name}")
        self.player_window.geometry("1000x700")
        self.player_window.configure(bg='#1a1a1a')
        
        # Main frame
        main_frame = ttk.Frame(self.player_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"🎤 {self.song_name}", 
                               font=('Arial', 20, 'bold'),
                               background='#1a1a1a', foreground='#ffffff')
        title_label.pack(pady=(0, 20))
        
        # Control buttons
        self.setup_controls(main_frame)
        
        # Progress bar
        self.setup_progress(main_frame)
        
        # Lyrics display
        self.setup_lyrics_display(main_frame)
        
        # Status
        self.setup_status(main_frame)
    
    def setup_controls(self, parent):
        """Setup player controls"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Play/Pause button
        self.play_btn = ttk.Button(controls_frame, text="▶️ Play",
                                  command=self.toggle_play,
                                  width=15)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        stop_btn = ttk.Button(controls_frame, text="⏹️ Stop",
                             command=self.stop_playback,
                             width=15)
        stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Restart button
        restart_btn = ttk.Button(controls_frame, text="🔄 Restart",
                                command=self.restart_playback,
                                width=15)
        restart_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Time display
        self.time_var = tk.StringVar(value="00:00 / 00:00")
        time_label = ttk.Label(controls_frame, textvariable=self.time_var,
                              font=('Arial', 12, 'bold'))
        time_label.pack(side=tk.RIGHT)
    
    def setup_progress(self, parent):
        """Setup progress bar"""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Click to seek functionality
        self.progress_bar.bind("<Button-1>", self.seek_to_position)
    
    def setup_lyrics_display(self, parent):
        """Setup lyrics display area"""
        lyrics_frame = ttk.LabelFrame(parent, text="Lyrics", padding="15")
        lyrics_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create canvas for lyrics with scrolling
        canvas_frame = ttk.Frame(lyrics_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.lyrics_canvas = tk.Canvas(canvas_frame, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.lyrics_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.lyrics_canvas)
        
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
                           font=('Arial', 16),
                           bg='#2c3e50',
                           fg='#bdc3c7',
                           wraplength=800,
                           justify=tk.LEFT,
                           pady=10)
            label.pack(fill=tk.X, padx=20, pady=5)
            self.lyrics_labels.append(label)
    
    def setup_status(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready to play")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                font=('Arial', 10))
        status_label.pack(side=tk.LEFT)
        
        # Segment info
        self.segment_var = tk.StringVar(value=f"0 / {len(self.segments)} segments")
        segment_label = ttk.Label(status_frame, textvariable=self.segment_var,
                                 font=('Arial', 10))
        segment_label.pack(side=tk.RIGHT)
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start playback"""
        self.is_playing = True
        self.start_time = time.time() - self.current_time
        self.play_btn.config(text="⏸️ Pause")
        
        # Start audio playback (simplified - you might want to integrate with pygame or similar)
        self.status_var.set("Playing...")
        
        # Start update loop
        self.update_player()
    
    def pause_playback(self):
        """Pause playback"""
        self.is_playing = False
        self.play_btn.config(text="▶️ Play")
        self.status_var.set("Paused")
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        self.current_time = 0
        self.current_segment = -1
        self.play_btn.config(text="▶️ Play")
        self.status_var.set("Stopped")
        self.update_lyrics_display()
    
    def restart_playback(self):
        """Restart playback from beginning"""
        self.stop_playback()
        self.start_playback()
    
    def update_player(self):
        """Update player state and lyrics"""
        if self.is_playing:
            self.current_time = time.time() - self.start_time
            
            # Update progress
            if self.segments:
                total_duration = self.segments[-1]['end_time']
                progress = (self.current_time / total_duration) * 100
                self.progress_var.set(min(progress, 100))
                
                # Update time display
                current_minutes = int(self.current_time // 60)
                current_seconds = int(self.current_time % 60)
                total_minutes = int(total_duration // 60)
                total_seconds = int(total_duration % 60)
                
                self.time_var.set(f"{current_minutes:02d}:{current_seconds:02d} / {total_minutes:02d}:{total_seconds:02d}")
            
            # Update lyrics
            self.update_lyrics_display()
            
            # Schedule next update
            self.player_window.after(100, self.update_player)
    
    def update_lyrics_display(self):
        """Update lyrics highlighting"""
        new_segment = -1
        
        # Find current segment
        for i, segment in enumerate(self.segments):
            if segment['start_time'] <= self.current_time <= segment['end_time']:
                new_segment = i
                break
        
        # Update segment highlighting
        if new_segment != self.current_segment:
            # Remove previous highlighting
            if self.current_segment >= 0:
                self.lyrics_labels[self.current_segment].config(
                    fg='#bdc3c7', bg='#2c3e50', font=('Arial', 16)
                )
            
            # Highlight current segment
            if new_segment >= 0:
                self.lyrics_labels[new_segment].config(
                    fg='#ffffff', bg='#3498db', font=('Arial', 18, 'bold')
                )
                
                # Scroll to current line
                self.scroll_to_segment(new_segment)
            
            self.current_segment = new_segment
            
            # Update segment counter
            current_num = new_segment + 1 if new_segment >= 0 else 0
            self.segment_var.set(f"{current_num} / {len(self.segments)} segments")
        
        # Word-level highlighting (if word timings available)
        if new_segment >= 0 and 'word_timings' in self.segments[new_segment]:
            self.update_word_highlighting(new_segment)
    
    def update_word_highlighting(self, segment_index):
        """Update word-level highlighting within current segment"""
        segment = self.segments[segment_index]
        if not segment.get('word_timings'):
            return
        
        # Find current word
        current_word = -1
        for i, word_timing in enumerate(segment['word_timings']):
            if word_timing['start'] <= self.current_time <= word_timing['end']:
                current_word = i
                break
        
        if current_word != self.current_word:
            # This is a simplified version - full implementation would need
            # more complex text manipulation for individual word highlighting
            self.current_word = current_word
    
    def scroll_to_segment(self, segment_index):
        """Scroll lyrics to show current segment"""
        if 0 <= segment_index < len(self.lyrics_labels):
            label = self.lyrics_labels[segment_index]
            label.update_idletasks()
            
            # Calculate position to scroll to
            total_height = self.scrollable_frame.winfo_reqheight()
            label_y = label.winfo_y()
            canvas_height = self.lyrics_canvas.winfo_height()
            
            if total_height > canvas_height:
                fraction = label_y / total_height
                self.lyrics_canvas.yview_moveto(max(0, fraction - 0.3))
    
    def seek_to_position(self, event):
        """Seek to position based on progress bar click"""
        if self.segments:
            total_duration = self.segments[-1]['end_time']
            click_position = event.x / self.progress_bar.winfo_width()
            new_time = click_position * total_duration
            
            self.current_time = new_time
            if self.is_playing:
                self.start_time = time.time() - self.current_time
            
            self.update_lyrics_display()
    
    def show(self):
        """Show the karaoke player window"""
        self.player_window.deiconify()
        self.player_window.lift()

def main():
    """Main function to run the karaoke GUI"""
    # Check if we're in the right directory structure
    current_dir = Path(__file__).parent  # src/GUI/
    src_dir = current_dir.parent  # src/
    root_dir = src_dir.parent  # noraemong/
    
    if not src_dir.exists():
        print("❌ Error: 'src' directory not found!")
        print("Please run this script from the correct location")
        print("Expected structure:")
        print("noraemong/")
        print("├── src/")
        print("│   ├── GUI/")
        print("│   │   ├── gui.py (this file)")
        print("│   │   └── karaoke_player.py")
        print("│   ├── audio/seperate.py")
        print("│   ├── lyrics/transcribe_vocal.py")
        print("│   └── sync/sync_lyrics.py")
        print("└── data/")
        return
    
    # Create and run GUI
    app = KaraokeGUI()
    app.run()

if __name__ == "__main__":
    main()