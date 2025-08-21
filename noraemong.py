#!/usr/bin/env python3
"""
Noraemong Karaoke Machine - Universal Launcher
Automatically detects available interfaces and dependencies
"""

import sys
import os
import subprocess
from pathlib import Path
import platform

def print_banner():
    """Print Noraemong banner"""
    print("🎤" + "=" * 50 + "🎤")
    print("    Noraemong Karaoke Machine")
    print("    Transform any song into karaoke!")
    print("🎤" + "=" * 50 + "🎤")
    print()

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def check_dependencies():
    """Check critical dependencies"""
    critical_deps = ['torch', 'librosa', 'faster_whisper', 'demucs']
    missing = []
    
    for dep in critical_deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    return missing

def install_tkinter_instructions():
    """Show tkinter installation instructions"""
    system = platform.system().lower()
    
    print("🔧 To install tkinter:")
    if system == "linux":
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  CentOS/RHEL:   sudo yum install tkinter")
        print("  Arch Linux:    sudo pacman -S tk")
    elif system == "darwin":
        print("  macOS: tkinter should be included with Python")
        print("  If missing, reinstall Python from python.org")
    elif system == "windows":
        print("  Windows: tkinter should be included with Python")
        print("  If missing, reinstall Python from python.org")
    else:
        print("  Check your system's package manager for python3-tk")

def get_python_command():
    """Get the correct Python command for this system"""
    import subprocess
    import platform
    
    # Windows typically uses 'python', Unix-like systems use 'python3'
    if platform.system() == "Windows":
        commands = ['python', 'py', 'python3']
    else:
        commands = ['python3', 'python', 'py']
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Python 3' in result.stdout:
                return cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    # Default fallback based on system
    return 'python' if platform.system() == "Windows" else 'python3'

def detect_os():
    """Detect operating system"""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "mac"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"

def ask_user_os():
    """Ask user to confirm their operating system"""
    detected_os = detect_os()
    
    print(f"🔍 Detected OS: {detected_os}")
    print("\n🖥️ Please confirm your operating system:")
    print("1. 🪟 Windows")
    print("2. 🍎 macOS") 
    print("3. 🐧 Linux")
    print("4. ❓ Other/Auto-detect")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        return "windows"
    elif choice == "2":
        return "mac"
    elif choice == "3":
        return "linux"
    elif choice == "4":
        return detected_os
    else:
        print(f"⚠️ Invalid choice, using detected OS: {detected_os}")
        return detected_os

def run_setup():
    """Run the appropriate setup script based on OS"""
    print("🔧 Starting setup process...")
    
    # Ask user for OS confirmation
    user_os = ask_user_os()
    python_cmd = get_python_command()
    
    print(f"\n🎯 Setting up for: {user_os}")
    print(f"🐍 Using Python command: {python_cmd}")
    
    # Determine which setup script to run
    if user_os == "windows":
        setup_script = "setup_noraemong_win.py"
    else:  # mac, linux, or unknown
        setup_script = "setup_noraemong_mac.py"
    
    setup_path = Path(__file__).parent / setup_script
    
    if setup_path.exists():
        print(f"🚀 Running {setup_script}...")
        try:
            result = subprocess.run([python_cmd, str(setup_path)], 
                                  check=False, text=True)
            if result.returncode == 0:
                print("✅ Setup completed successfully!")
            else:
                print("⚠️ Setup completed with some issues")
        except Exception as e:
            print(f"❌ Failed to run setup: {e}")
    else:
        print(f"❌ Setup script not found: {setup_script}")
        print("Please install dependencies manually:")
        if user_os == "windows":
            print("   python -m pip install torch librosa faster-whisper demucs fuzzywuzzy")
        else:
            print("   python3 -m pip install torch librosa faster-whisper demucs fuzzywuzzy")

def run_gui_mode():
    """Run GUI mode"""
    gui_path = Path(__file__).parent / "src" / "GUI" / "gui.py"
    python_cmd = get_python_command()
    
    if gui_path.exists():
        print(f"🖥️ Launching GUI mode with {python_cmd}...")
        try:
            subprocess.run([python_cmd, str(gui_path)], check=False)
        except Exception as e:
            print(f"❌ Failed to launch GUI: {e}")
    else:
        print("❌ GUI not found at src/GUI/gui.py")

def run_cli_mode():
    """Run CLI mode"""
    print("🌐 Starting CLI mode...")
    print("This mode will process your audio and launch web karaoke")
    print()
    
    # Import CLI function
    sys.path.append(str(Path(__file__).parent / "src" / "GUI"))
    try:
        from gui import run_web_only_mode
        run_web_only_mode()
    except ImportError as e:
        print(f"❌ Failed to import CLI mode: {e}")
        print("Please ensure all dependencies are installed")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check if we're in the right directory
    if not (Path(__file__).parent / "src").exists():
        print("❌ Error: Please run this from the noraemong root directory")
        print("Expected structure:")
        print("noraemong/")
        print("├── noraemong.py (this file)")
        print("├── setup_noraemong.py")
        print("└── src/")
        return
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"❌ Missing critical dependencies: {', '.join(missing_deps)}")
        print("🔧 Run setup first:")
        print("   python setup_noraemong.py")
        print()
        choice = input("Run setup now? (y/n): ").lower()
        if choice in ['y', 'yes']:
            run_setup()
            return
        else:
            print(f"Please install dependencies first with: {python_cmd} -m pip install [packages]")
            return
    
    # Check interface options
    has_tkinter = check_tkinter()
    
    if len(sys.argv) > 1:
        # Command line arguments
        mode = sys.argv[1].lower()
        if mode in ['gui', '--gui']:
            if has_tkinter:
                run_gui_mode()
            else:
                print("❌ GUI mode not available (tkinter missing)")
                install_tkinter_instructions()
        elif mode in ['cli', '--cli', 'web', '--web']:
            run_cli_mode()
        elif mode in ['setup', '--setup']:
            run_setup()
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Available modes: gui, cli, setup")
    else:
        # Interactive mode
        print("🎯 Choose your interface:")
        options = []
        
        if has_tkinter:
            print("1. 🖥️  GUI Mode (Graphical Interface)")
            options.append(('1', 'gui'))
        else:
            print("1. ❌ GUI Mode (tkinter not available)")
        
        print("2. 🌐 Web Mode (Command Line + Browser)")
        options.append(('2', 'cli'))
        
        print("3. 🔧 Setup (Install Dependencies)")
        options.append(('3', 'setup'))
        
        print("4. ❌ Exit")
        options.append(('4', 'exit'))
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        # Find selected option
        selected = None
        for opt_num, opt_mode in options:
            if choice == opt_num:
                selected = opt_mode
                break
        
        if selected == 'gui':
            if has_tkinter:
                run_gui_mode()
            else:
                print("❌ GUI not available")
                if check_and_offer_tkinter_install():
                    run_gui_mode()
                else:
                    print("🌐 Switching to web mode...")
                    run_cli_mode()
        elif selected == 'cli':
            run_cli_mode()
        elif selected == 'setup':
            run_setup()
        elif selected == 'exit':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    
    if not has_tkinter:
        print("\n💡 Note: For full GUI experience, install tkinter:")
        install_tkinter_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("🆘 If this persists, please check the GitHub issues page")