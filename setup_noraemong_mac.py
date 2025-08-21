"""
Noraemong Karaoke Machine Setup Script - macOS/Linux Version
Installs all required dependencies for macOS and Linux systems.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    system_name = "macOS" if platform.system() == "Darwin" else "Linux"
    print("=" * 60)
    print(f"🎤 Noraemong Karaoke Machine Setup - {system_name}")
    print("=" * 60)
    print()

def get_python_command():
    """Get the correct Python command for this system"""
    commands = ['python3', 'python', 'py']
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Python 3' in result.stdout:
                return cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    return 'python3'

def check_python_version():
    """Check if Python version is compatible"""
    python_cmd = get_python_command()
    print(f"🐍 Checking Python version (using {python_cmd})...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Noraemong requires Python 3.8 or higher")
        if platform.system() == "Darwin":
            print("   Download from: https://www.python.org/downloads/macos/")
        else:
            print("   Install with your package manager or from python.org")
        return False

def install_package(package_name, import_name=None, extra_args=None):
    """Install a Python package using pip"""
    python_cmd = get_python_command()
    
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} already installed")
        return True
    except ImportError:
        print(f"📦 Installing {package_name}...")
        
        try:
            cmd = [python_cmd, "-m", "pip", "install", package_name]
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

def install_pytorch_mac_linux():
    """Install PyTorch for macOS/Linux"""
    system = platform.system()
    print(f"🔥 Installing PyTorch for {system}...")
    
    try:
        import torch
        import torchaudio
        print("✅ PyTorch already installed")
        return True
    except ImportError:
        pass
    
    python_cmd = get_python_command()
    
    if system == "Darwin":  # macOS
        # For macOS, use CPU version for better compatibility
        print("📦 Installing PyTorch (CPU version for macOS compatibility)...")
        cmd = [python_cmd, "-m", "pip", "install", "torch", "torchaudio", 
               "--index-url", "https://download.pytorch.org/whl/cpu"]
    else:  # Linux
        # For Linux, try CPU first, then CUDA if available
        print("📦 Installing PyTorch (CPU version)...")
        cmd = [python_cmd, "-m", "pip", "install", "torch", "torchaudio", 
               "--index-url", "https://download.pytorch.org/whl/cpu"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyTorch installed successfully")
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

def test_and_install_tkinter():
    """Test tkinter and attempt to install if missing"""
    print("\n🖥️ Testing GUI support (tkinter)...")
    
    try:
        import tkinter
        print("✅ tkinter available - GUI mode supported!")
        return True
    except ImportError:
        print("❌ tkinter not available - GUI mode not supported")
        print("\n💡 tkinter is required for the graphical interface")
        
        response = input("Would you like to try auto-installing tkinter? (y/n): ").lower()
        if response in ['y', 'yes']:
            if install_tkinter():
                # Test again after installation
                try:
                    import tkinter
                    print("🎉 tkinter now working! GUI mode available!")
                    return True
                except ImportError:
                    print("❌ tkinter still not working after installation")
                    print_manual_tkinter_instructions()
                    return False
            else:
                print("❌ Auto-installation failed")
                print_manual_tkinter_instructions()
                return False
        else:
            print("ℹ️ Skipping tkinter installation")
            print("🌐 You can still use web mode")
            return False

def install_tkinter():
    """Attempt to install tkinter on various systems"""
    print("🔧 Installing tkinter...")
    
    system = platform.system().lower()
    
    try:
        if system == "linux":
            # Detect Linux distribution
            if os.path.exists("/etc/debian_version"):
                # Debian/Ubuntu
                print("📦 Installing python3-tk (Debian/Ubuntu)...")
                result = subprocess.run(["sudo", "apt-get", "update"], capture_output=True)
                result = subprocess.run(["sudo", "apt-get", "install", "-y", "python3-tk"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ tkinter installed successfully!")
                    return True
                else:
                    print(f"❌ Failed: {result.stderr}")
                    
            elif os.path.exists("/etc/redhat-release") or os.path.exists("/etc/fedora-release"):
                # RedHat/CentOS/Fedora
                print("📦 Installing python3-tkinter (RedHat/CentOS/Fedora)...")
                # Try dnf first, then yum
                for cmd in ["dnf", "yum"]:
                    try:
                        result = subprocess.run(["sudo", cmd, "install", "-y", "python3-tkinter"], 
                                              capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            print("✅ tkinter installed successfully!")
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                        
            elif os.path.exists("/etc/arch-release"):
                # Arch Linux
                print("📦 Installing tk (Arch Linux)...")
                result = subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "tk"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ tkinter installed successfully!")
                    return True
                    
        elif system == "darwin":
            # macOS
            print("📦 Installing python-tk (macOS with Homebrew)...")
            try:
                # Check if Homebrew is installed
                subprocess.run(["brew", "--version"], capture_output=True, timeout=5)
                result = subprocess.run(["brew", "install", "python-tk"], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print("✅ tkinter installed successfully!")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️ Homebrew not found.")
                print("   Install Homebrew from: https://brew.sh")
                print("   Then run: brew install python-tk")
                
    except Exception as e:
        print(f"❌ Auto-install failed: {e}")
    
    return False

def print_manual_tkinter_instructions():
    """Print manual installation instructions for tkinter"""
    system = platform.system().lower()
    python_cmd = get_python_command()
    
    print("\n📋 Manual tkinter installation:")
    if system == "linux":
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  CentOS/RHEL:   sudo dnf install python3-tkinter")
        print("  Fedora:        sudo dnf install python3-tkinter") 
        print("  Arch Linux:    sudo pacman -S tk")
    elif system == "darwin":
        print("  macOS:")
        print("    1. Install Homebrew: https://brew.sh")
        print("    2. Run: brew install python-tk")
        print("    OR reinstall Python from python.org")
    
    print(f"\n🧪 Test with: {python_cmd} -c 'import tkinter; print(\"tkinter works!\")'")

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

def check_system_requirements():
    """Check system requirements"""
    system_name = "macOS" if platform.system() == "Darwin" else "Linux"
    print(f"\n💻 Checking {system_name} requirements...")
    
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
    
    # Check memory (if psutil available)
    try:
        import psutil
        total_memory = psutil.virtual_memory().total / (1024 * 1024 * 1024)  # GB
        if total_memory >= 4:
            print(f"✅ Memory: {total_memory:.1f} GB")
        else:
            print(f"⚠️ Limited memory: {total_memory:.1f} GB (recommend 4+ GB)")
    except ImportError:
        print("ℹ️ Could not check memory (psutil not available)")
    
    # macOS-specific checks
    if platform.system() == "Darwin":
        print("🍎 macOS-specific checks:")
        try:
            # Check Xcode Command Line Tools
            result = subprocess.run(["xcode-select", "-p"], capture_output=True)
            if result.returncode == 0:
                print("✅ Xcode Command Line Tools installed")
            else:
                print("⚠️ Xcode Command Line Tools not found")
                print("   Install with: xcode-select --install")
        except FileNotFoundError:
            print("⚠️ Xcode Command Line Tools not found")
            print("   Install with: xcode-select --install")
        
        # Check Homebrew
        try:
            result = subprocess.run(["brew", "--version"], capture_output=True)
            if result.returncode == 0:
                print("✅ Homebrew available")
            else:
                print("ℹ️ Homebrew not found (optional)")
                print("   Install from: https://brew.sh")
        except FileNotFoundError:
            print("ℹ️ Homebrew not found (optional)")
            print("   Install from: https://brew.sh")

def print_usage_instructions():
    """Print usage instructions"""
    python_cmd = get_python_command()
    
    print("\n📖 Usage Instructions:")
    print("=" * 40)
    print("1. Run the main GUI:")
    print(f"   {python_cmd} src/GUI/gui.py")
    print()
    print("2. Or use the universal launcher:")
    print(f"   {python_cmd} noraemong.py")
    print()
    print("3. Web-only mode:")
    print(f"   {python_cmd} noraemong.py cli")
    print()
    print("4. Individual modules:")
    print(f"   {python_cmd} src/audio/seperate.py <audio_file>")
    print(f"   {python_cmd} src/lyrics/transcribe_vocal.py <audio_file>")
    print(f"   {python_cmd} src/sync/sync_lyrics.py <audio_file> <lyrics_file>")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return False
    
    print()
    
    # Install PyTorch first
    if not install_pytorch_mac_linux():
        print("\n❌ Setup failed: Could not install PyTorch")
        return False
    
    # Install core dependencies
    if not install_core_dependencies():
        print("\n⚠️ Some core dependencies failed to install")
        print("   The application may not work correctly")
    
    # Test and install tkinter
    gui_available = test_and_install_tkinter()
    
    # Check system requirements
    check_system_requirements()
    
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
            python_cmd = get_python_command()
            print(f"\n📖 Usage: {python_cmd} noraemong.py cli")
        
        print(f"\n✨ Ready to make some karaoke! 🎤")
        
        # Ask if user wants to launch
        try:
            python_cmd = get_python_command()
            response = input("\nWould you like to launch Noraemong now? (y/n): ").lower()
            if response in ['y', 'yes']:
                print("🚀 Launching Noraemong...")
                subprocess.run([python_cmd, "noraemong.py"])
        except KeyboardInterrupt:
            python_cmd = get_python_command()
            print(f"\n👋 Setup complete! Run '{python_cmd} noraemong.py' when ready.")
        
        return True
    else:
        print("\n❌ Setup completed with errors")
        print("   Some features may not work correctly")
        print("   Try running the setup again or install missing packages manually")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        python_cmd = get_python_command()
        print("\n🆘 Need help?")
        print(f"   1. Try running: {python_cmd} setup_noraemong_mac.py --quick-fix")
        print("   2. Check the GitHub issues page for known problems")
        if platform.system() == "Darwin":
            print("   3. Make sure Xcode Command Line Tools are installed")
        else:
            print("   3. Make sure build tools are installed for your distribution")