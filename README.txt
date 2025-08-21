# 🎤 Noraemong Karaoke Machine

**Transform any song into a professional karaoke experience with AI-powered vocal separation and synchronized lyrics!**

## ✨ Features

- 🎵 **AI-Powered Vocal Separation** - Remove vocals from any song using Facebook's Demucs
- 🎤 **Automatic Lyrics Generation** - Extract lyrics from vocal tracks using Whisper AI
- 📝 **Custom Lyrics Support** - Use your own lyrics files for perfect accuracy
- ⏱️ **Smart Lyrics Synchronization** - Align lyrics with music timing automatically
- 🎬 **Professional Karaoke Player** - Desktop and web-based players with real-time highlighting
- 🌐 **Multi-Format Support** - MP3, WAV, FLAC, M4A audio files
- 📱 **Responsive Design** - Works on desktop and mobile devices

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
# Clone or download the project
git clone https://github.com/yourusername/noraemong
cd noraemong

# Run the universal launcher - it will ask for your OS and run the right setup
python noraemong.py
# Choose option 3 (Setup) and follow prompts

# OR run setup directly:
# Windows:
python setup_noraemong_win.py

# macOS/Linux:
python3 setup_noraemong_mac.py
```

### 2. Launch the Application

```bash
# Universal launcher (detects best interface)
# Windows:
python noraemong.py

# macOS/Linux:
python3 noraemong.py

# Or web-only mode (works on any system):
# Windows:
python noraemong.py cli

# macOS/Linux:  
python3 noraemong.py cli
```

### 3. Create Your Karaoke

1. **Select Audio File** - Choose your favorite song (MP3, WAV, FLAC, M4A)
2. **Choose Processing Mode:**
   - 🤖 **Auto-generate lyrics** - AI extracts and creates lyrics automatically
   - 📝 **Use custom lyrics** - Upload your own lyrics file for perfect accuracy
3. **Start Processing** - Let AI separate vocals and sync lyrics
4. **Launch Karaoke Player** - Enjoy professional karaoke with highlighted lyrics!

## 📁 Project Structure

```
noraemong/
├── setup_noraemong_win.py      # Windows setup script
├── setup_noraemong_mac.py      # macOS/Linux setup script  
├── noraemong.py                # Universal launcher
├── src/
│   ├── GUI/
│   │   ├── gui.py              # Main GUI application
│   │   └── karaoke_player.py   # Enhanced karaoke player
│   ├── audio/
│   │   └── seperate.py         # Vocal/instrumental separation
│   ├── lyrics/
│   │   └── transcribe_vocal.py # Lyrics transcription
│   ├── sync/
│   │   └── sync_lyrics.py      # Lyrics synchronization
│   └── player/
│       └── lyrics_video_player.py  # Web player
└── data/                       # Output files
    ├── separate/              # Separated audio files
    ├── transcribe_vocal/      # Generated lyrics
    └── sync_output/           # Synchronized lyrics
```

## 🛠️ Manual Installation

If the setup script doesn't work, install dependencies manually:

### Core Requirements

```bash
# Python 3.8+ required
python --version

# Core audio processing
pip install librosa soundfile scipy numpy

# AI models
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install faster-whisper demucs

# Text processing
pip install fuzzywuzzy python-levenshtein

# GUI and player
pip install pygame tkinter

# Optional enhancements
pip install matplotlib pillow requests
```

### Platform-Specific Notes

**Windows:**
- Install Visual C++ Build Tools if you get compilation errors
- For CUDA support: Use `--index-url https://download.pytorch.org/whl/cu118`

**macOS:**
- Install Xcode Command Line Tools: `xcode-select --install`
- Use CPU version of PyTorch for better compatibility

**Linux:**
- Install system audio libraries: `sudo apt-get install libasound2-dev`
- For CUDA: Check your CUDA version and install matching PyTorch

## 🎮 Usage Modes

### GUI Mode (Recommended)
```bash
# Universal launcher (asks for your OS)
python noraemong.py           # Windows
python3 noraemong.py          # macOS/Linux

# Choose option 1 (GUI) if tkinter available
```
User-friendly interface with step-by-step guidance.

### Web Mode (No GUI needed)
```bash
# Web-only mode (works on any system)
python noraemong.py cli       # Windows
python3 noraemong.py cli      # macOS/Linux
```
Command-line setup + browser-based karaoke player.

### Command Line Mode

**Separate vocals:**
```bash
# Windows:
python src/audio/seperate.py song.mp3

# macOS/Linux:
python3 src/audio/seperate.py song.mp3
```

**Generate lyrics:**
```bash
# Windows:
python src/lyrics/transcribe_vocal.py song_vocals_clean.wav

# macOS/Linux:
python3 src/lyrics/transcribe_vocal.py song_vocals_clean.wav
```

**Sync custom lyrics:**
```bash
# Windows:
python src/sync/sync_lyrics.py song.mp3 my_lyrics.txt

# macOS/Linux:
python3 src/sync/sync_lyrics.py song.mp3 my_lyrics.txt
```

## 🎛️ Karaoke Player Features

### Desktop Player
- 🎵 High-quality audio playback
- 📜 Scrolling lyrics with word-level highlighting
- ⌨️ Keyboard shortcuts (Space=Play/Pause, ←→=Seek, ↑↓=Font size)
- 🖥️ Fullscreen mode (F11)
- 🔊 Volume control
- 🎯 Click lyrics to seek

### Web Player
- 🌐 Works in any modern browser
- 📱 Mobile-responsive design
- 🎨 Beautiful gradient backgrounds
- ⚡ Real-time lyrics synchronization
- 🎬 Professional karaoke styling

### Keyboard Shortcuts
- `Space` - Play/Pause
- `←/→` - Seek backward/forward 10 seconds
- `↑/↓` - Increase/decrease font size
- `F11` - Toggle fullscreen
- `Esc` - Exit fullscreen

## ⚙️ Configuration Options

### Audio Quality Settings
- **Fast** - Quick processing, good quality
- **Medium** - Balanced speed and quality (recommended)
- **High** - Best quality, slower processing

### Device Selection
- **Auto** - Automatically choose best available device
- **CPU** - Use CPU processing (compatible, slower)
- **CUDA** - Use GPU acceleration (fastest, requires NVIDIA GPU)

### Lyrics Processing
- **Similarity Threshold** - Adjust lyrics matching sensitivity (0.4-0.8)
- **Language** - Specify audio language for better transcription
- **Model Size** - Choose Whisper model size (base/large for quality vs speed)

## 🔧 Troubleshooting

### Common Issues

**"tkinter not found"**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL/Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk

# macOS (with Homebrew)
brew install python-tk

# Test it works
python3 -c "import tkinter; print('tkinter works!')"
```

**"python command not found"**
```bash
# Use python3 instead
python3 noraemong.py

# Or install python alias
alias python=python3
```

**"Audio playback not working"**
- Install pygame: `pip install pygame`
- Check system audio drivers
- Try different audio formats

**"Slow processing"**
- Use "Fast" quality setting
- Close other applications
- Use smaller audio files for testing

### Performance Tips

1. **Use SSD storage** for faster file I/O
2. **Close other applications** during processing
3. **Use CUDA** if you have NVIDIA GPU
4. **Convert to WAV** for best compatibility
5. **Trim audio files** to song length only

## 🎯 Best Practices

### For Best Vocal Separation:
- Use high-quality source audio (320kbps+ MP3 or lossless)
- Avoid heavily compressed or low-quality files
- Songs with clear vocal/instrumental separation work best
- Acoustic or pop songs typically separate better than heavy metal

### For Accurate Lyrics:
- Use custom lyrics files when possible
- Choose "large" Whisper model for better accuracy
- Specify the correct language
- Clean audio (separated vocals) gives better transcription

### For Smooth Playback:
- Ensure audio files are in the same directory as sync data
- Use modern browser for web player
- Close unnecessary applications during playback
- Test with shorter songs first

## 🤝 Contributing

We welcome contributions! Areas for improvement:

- 🎵 Better vocal separation algorithms
- 🌍 Multi-language support
- 🎨 UI/UX improvements
- 📱 Mobile app development
- 🎤 Real-time karaoke features

## 📄 License

This project is open source. See individual module licenses for details.

## 🙏 Acknowledgments

- **Facebook Demucs** - State-of-the-art music source separation
- **OpenAI Whisper** - Robust speech recognition
- **PyTorch** - Deep learning framework
- **Librosa** - Audio analysis library

## 🆘 Support

Having issues? Try these steps:

1. **Run setup again**: `python setup_noraemong.py --quick-fix`
2. **Check requirements**: Python 3.8+, 4GB+ RAM, 2GB+ disk space
3. **Update dependencies**: `pip install --upgrade torch librosa faster-whisper`
4. **Test individual modules** before using the GUI
5. **Check GitHub issues** for known problems and solutions

---

**Made with ❤️ for karaoke lovers everywhere! 🎤✨**

*Transform any song into your personal karaoke stage!*