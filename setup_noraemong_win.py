"""
Noraemong Karaoke Machine Setup Script - Windows Version
Installs all required dependencies for Windows systems.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🎤 Noraemong Karaoke Machine Setup - Windows")
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
        print("   Download from: https://www.python.org/downloads/windows/")
        return False

def install_package(package_name, import_name=None, extra_args=None):
    """Install a Python package using pip"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} already installed")
        return True
    except ImportError:
        print(f"📦 Installing {package_name}...")
        
        try:
            cmd = ["python", "-m", "pip", "install", package_name]
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

def install_pytorch_windows():
    """Install PyTorch for Windows"""
    print("🔥 Installing PyTorch for Windows...")
    
    try:
        import torch
        import torchaudio
        print("✅ PyTorch already installed")
        return True
    except ImportError:
        pass
    
    # Windows PyTorch installation
    print("📦 Installing PyTorch with CPU support...")
    cmd = ["python", "-m", "pip", "install", "torch", "torchaudio", 
           "--index-url", "https://download.pytorch.org/whl/cpu"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyTorch installed successfully")
            return True
        else:
            print("⚠️ CPU PyTorch failed, trying CUDA version...")
            # Try CUDA version
            cuda_cmd = ["python", "-m", "pip", "install", "torch", "torchaudio", 
                       "--index-url", "https://download.pytorch.org/whl/cu118"]
            result = subprocess.run(cuda_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PyTorch (CUDA) installed successfully")
                return True
            else:
                print(f"❌ Failed to install PyTorch: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Exception installing PyTorch: {e}")
        return False

def install_core_dependencies():
    """Install core dependencies for Windows"""
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

def test_and_fix_tkinter_windows():
    """Test and fix tkinter on Windows"""
    print("\n🖥️ Testing GUI support (tkinter)...")
    
    try:
        import tkinter
        print("✅ tkinter available - GUI mode supported!")
        return True
    except ImportError:
        print("❌ tkinter not available")
        print("\n🔧 Fixing tkinter on Windows...")
        print("📝 tkinter should be included with Python on Windows")
        print("💡 This usually means Python was not installed with tkinter")
        
        print("\n🛠️ Attempting to fix...")
        try:
            # Try to reinstall/update tkinter components
            result = subprocess.run(["python", "-m", "pip", "install", "--upgrade", "tk"], 
                                  capture_output=True, text=True)
            
            # Try importing again
            import tkinter
            print("✅ tkinter fixed!")
            return True
            
        except ImportError:
            print("❌ Could not fix tkinter automatically")
            print("\n📋 Manual fix required:")
            print("   1. Download Python from: https://www.python.org/downloads/windows/")
            print("   2. During installation, make sure to check:")
            print("      ✅ 'tcl/tk and IDLE' option")
            print("      ✅ 'Python test suite'")
            print("   3. Reinstall Python with these options")
            print("\n🌐 Alternative: You can still use web mode")
            
            response = input("Continue setup without GUI? (y/n): ").lower()
            return response in ['y', 'yes']

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

def check_windows_requirements():
    """Check Windows-specific requirements"""
    print("\n💻 Checking Windows requirements...")
    
    # Check Windows version
    try:
        win_version = platform.win32_ver()[1]
        print(f"✅ Windows version: {win_version}")
    except:
        print("⚠️ Could not detect Windows version")
    
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
    
    # Check if Visual C++ Build Tools are available (for some packages)
    print("🔧 Checking build tools...")
    try:
        result = subprocess.run(["cl"], capture_output=True, text=True)
        if "Microsoft" in result.stderr:
            print("✅ Visual C++ Build Tools available")
        else:
            print("⚠️ Visual C++ Build Tools not found")
            print("   Some packages may fail to install")
            print("   Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    except FileNotFoundError:
        print("ℹ️ Visual C++ Build Tools not in PATH (may not be needed)")

def print_usage_instructions():
    """Print usage instructions for Windows"""
    print("\n📖 Usage Instructions:")
    print("=" * 40)
    print("1. Run the main GUI:")
    print("   python src\\GUI\\gui.py")
    print()
    print("2. Or use the universal launcher:")
    print("   python noraemong.py")
    print()
    print("3. Web-only mode:")
    print("   python noraemong.py cli")
    print()
    print("4. Individual modules:")
    print("   python src\\audio\\seperate.py <audio_file>")
    print("   python src\\lyrics\\transcribe_vocal.py <audio_file>")
    print("   python src\\sync\\sync_lyrics.py <audio_file> <lyrics_file>")
    print()

def main():
    """Main setup function for Windows"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        input("Press Enter to exit...")
        return False
    
    print()
    
    # Install PyTorch first
    if not install_pytorch_windows():
        print("\n❌ Setup failed: Could not install PyTorch")
        input("Press Enter to exit...")
        return False
    
    # Install core dependencies
    if not install_core_dependencies():
        print("\n⚠️ Some core dependencies failed to install")
        print("   The application may not work correctly")
    
    # Test and fix tkinter
    gui_available = test_and_fix_tkinter_windows()
    
    # Check Windows requirements
    check_windows_requirements()
    
    # Create directories
    create_directory_structure()
    
    # Test imports
    print()
    if test_imports():
        print("\n🎉 Setup completed successfully!")
        
        if gui_available:
            print("🖥️ GUI mode available!")
            print_usage_instructions()
        else:
            print("🌐 Web mode available (GUI not supported)")
            print("\n📖 Usage:")
            print("   python noraemong.py cli")
        
        print(f"\n✨ Ready to make some karaoke! 🎤")
        
        # Ask if user wants to launch
        try:
            response = input("\nWould you like to launch Noraemong now? (y/n): ").lower()
            if response in ['y', 'yes']:
                print("🚀 Launching Noraemong...")
                subprocess.run(["python", "noraemong.py"])
        except KeyboardInterrupt:
            print("\n👋 Setup complete! Run 'python noraemong.py' when ready.")
        
        return True
    else:
        print("\n❌ Setup completed with errors")
        print("   Some features may not work correctly")
        print("   Try running the setup again or install missing packages manually")
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🆘 Need help?")
        print("   1. Make sure you have Python 3.8+ from python.org")
        print("   2. Run as Administrator if permission errors occur")
        print("   3. Check the GitHub issues page for known problems")
        input("Press Enter to exit...")