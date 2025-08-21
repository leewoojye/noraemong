"""
Noraemong Karaoke Machine Setup Script
Installs all required dependencies and checks system compatibility.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🎤 Noraemong Karaoke Machine Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Noraemong requires Python 3.8 or higher")
        return False

def install_package(package_name, import_name=None, extra_args=None):
    """Install a Python package"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} already installed")
        return True
    except ImportError:
        print(f"📦 Installing {package_name}...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", package_name]
            if extra_args:
                cmd.extend(extra_args)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package_name} installed successfully")
                return True
            else:
                print(f"❌ Failed to install {package_name}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Exception installing {package_name}: {e}")
            return False

def install_pytorch():
    """Install PyTorch with appropriate configuration"""
    print("🔥 Installing PyTorch...")
    
    try:
        import torch
        import torchaudio
        print("✅ PyTorch already installed")
        return True
    except ImportError:
        pass
    
    # Determine the best PyTorch installation command
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        # For macOS, use CPU version for better compatibility
        cmd = [sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
    elif system == "windows":
        # For Windows, try CUDA first, fallback to CPU
        cmd = [sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"]
    else:  # Linux
        cmd = [sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyTorch installed successfully")
            return True
        else:
            print("⚠️ CUDA PyTorch failed, trying CPU version...")
            # Fallback to CPU version
            cpu_cmd = [sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
            result = subprocess.run(cpu_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PyTorch (CPU) installed successfully")
                return True
            else:
                print(f"❌ Failed to install PyTorch: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Exception installing PyTorch: {e}")
        return False

def install_core_dependencies():
    """Install core dependencies"""
    print("\n📚 Installing core dependencies...")
    
    packages = [
        ("numpy", None),
        ("scipy", None),
        ("librosa", None),
        ("soundfile", None),
        ("faster-whisper", "faster_whisper"),
        ("fuzzywuzzy", None),
        ("python-levenshtein", "Levenshtein"),
        ("demucs", None),
        ("pygame", None),
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package, import_name in packages:
        if install_package(package, import_name):
            success_count += 1
    
    print(f"\n📊 Core dependencies: {success_count}/{total_count} installed successfully")
    return success_count == total_count

def install_optional_dependencies():
    """Install optional dependencies for enhanced features"""
    print("\n🎨 Installing optional dependencies...")
    
    optional_packages = [
        ("matplotlib", None),
        ("pillow", "PIL"),
        ("requests", None),
    ]
    
    for package, import_name in optional_packages:
        install_package(package, import_name)

def check_system_requirements():
    """Check system requirements"""
    print("\n💻 Checking system requirements...")
    
    # Check available disk space
    try:
        import shutil
        free_space = shutil.disk_usage(".").free / (1024 * 1024 * 1024)  # GB
        if free_space >= 2:
            print(f"✅ Disk space: {free_space:.1f} GB available")
        else:
            print(f"⚠️ Low disk space: {free_space:.1f} GB (recommend 2+ GB)")
    except:
        print("⚠️ Could not check disk space")
    
    # Check memory
    try:
        import psutil
        total_memory = psutil.virtual_memory().total / (1024 * 1024 * 1024)  # GB
        if total_memory >= 4:
            print(f"✅ Memory: {total_memory:.1f} GB")
        else:
            print(f"⚠️ Limited memory: {total_memory:.1f} GB (recommend 4+ GB)")
    except:
        print("ℹ️ Could not check memory (install psutil for memory info)")
    
    # Check for audio support
    print("🔊 Checking audio support...")
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.quit()
        print("✅ Audio support available (pygame)")
    except:
        print("⚠️ Audio support limited (pygame not working)")

def create_directory_structure():
    """Create required directory structure"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "data",
        "data/separate", 
        "data/transcribe_vocal",
        "data/sync_output"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")

def test_imports():
    """Test if all critical imports work"""
    print("\n🧪 Testing imports...")
    
    critical_imports = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
        ("librosa", "Librosa"),
        ("faster_whisper", "Faster Whisper"),
        ("demucs", "Demucs"),
        ("fuzzywuzzy", "FuzzyWuzzy"),
        ("pygame", "Pygame"),
        ("tkinter", "Tkinter (GUI)"),
    ]
    
    success_count = 0
    for module, name in critical_imports:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 Import test: {success_count}/{len(critical_imports)} successful")
    return success_count == len(critical_imports)

def print_usage_instructions():
    """Print usage instructions"""
    print("\n📖 Usage Instructions:")
    print("=" * 40)
    print("1. Run the main GUI:")
    print("   python src/GUI/gui.py")
    print()
    print("2. Or use individual modules:")
    print("   python src/audio/seperate.py <audio_file>")
    print("   python src/lyrics/transcribe_vocal.py <audio_file>")
    print("   python src/sync/sync_lyrics.py <audio_file> <lyrics_file>")
    print()
    print("3. Directory structure:")
    print("   noraemong/")
    print("   ├── setup_noraemong.py (this file)")
    print("   ├── src/")
    print("   │   ├── GUI/")
    print("   │   │   ├── gui.py (main application)")
    print("   │   │   └── karaoke_player.py (enhanced player)")
    print("   │   ├── audio/seperate.py")
    print("   │   ├── lyrics/transcribe_vocal.py")
    print("   │   ├── sync/sync_lyrics.py")
    print("   │   └── player/lyrics_video_player.py")
    print("   └── data/ (output files)")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        print("   Please install Python 3.8 or higher")
        return False
    
    print()
    
    # Install PyTorch first (most critical and complex)
    if not install_pytorch():
        print("\n❌ Setup failed: Could not install PyTorch")
        print("   PyTorch is required for AI processing")
        return False
    
    # Install core dependencies
    if not install_core_dependencies():
        print("\n⚠️ Some core dependencies failed to install")
        print("   The application may not work correctly")
    
    # Install optional dependencies
    install_optional_dependencies()
    
    # Check system requirements
    check_system_requirements()
    
    # Create directories
    create_directory_structure()
    
    # Test imports
    print()
    if test_imports():
        print("\n🎉 Setup completed successfully!")
        print_usage_instructions()
        
        # Test the GUI
        print("\n🚀 Testing GUI launch...")
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the test window
            root.destroy()
            print("✅ GUI system working")
        except Exception as e:
            print(f"❌ GUI test failed: {e}")
        
        return True
    else:
        print("\n❌ Setup completed with errors")
        print("   Some features may not work correctly")
        print("   Try running the setup again or install missing packages manually")
        return False

def quick_fix():
    """Quick fix for common issues"""
    print("🔧 Running quick fixes...")
    
    # Update pip
    print("📦 Updating pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                  capture_output=True)
    
    # Fix common dependency conflicts
    print("🔄 Fixing dependency conflicts...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], 
                  capture_output=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Noraemong Karaoke Machine")
    parser.add_argument("--quick-fix", action="store_true", 
                       help="Run quick fixes for common issues")
    
    args = parser.parse_args()
    
    if args.quick_fix:
        quick_fix()
    
    success = main()
    
    if not success:
        print("\n🆘 Need help? Try:")
        print("   python setup_noraemong.py --quick-fix")
        print("   Or check the GitHub issues page")
        sys.exit(1)
    else:
        print("\n✨ Ready to make some karaoke! 🎤")
        
        # Ask if user wants to launch the GUI
        try:
            response = input("\nWould you like to launch the GUI now? (y/n): ").lower()
            if response in ['y', 'yes']:
                print("🚀 Launching Noraemong GUI...")
                subprocess.run([sys.executable, "src/GUI/gui.py"])
        except KeyboardInterrupt:
            print("\n👋 Setup complete! Run 'python src/GUI/gui.py' when ready.")