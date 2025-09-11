#!/usr/bin/env python3
"""
Build script for serial communication tool using PyInstaller
"""
import os
import subprocess
import sys
import shutil


def build():
    """Build the application using PyInstaller"""

    # Check if PyInstaller is available
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                      check=True)

    # Clean previous builds
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # Clean spec files
    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)

    # Determine path separator based on OS
    separator = ";" if os.name == "nt" else ":"

    # PyInstaller command using python -m
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        "--onefile",
        "--windowed",
        "--name", "serial_tool",
        f"--add-data=README.md{separator}.",
        f"--add-data=doc/USAGE.md{separator}.",
        f"--add-data=doc/PAIRING_GUIDE.md{separator}.",
        "main.py"
    ]

    print("Building with PyInstaller...")
    print("Command:", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Build completed successfully!")
        exe_name = "serial_tool.exe" if os.name == "nt" else "serial_tool"
        print(f"Executable location: dist/{exe_name}")
        return True
    except subprocess.CalledProcessError as e:
        print("Build failed!")
        print("Error:", e.stderr)
        return False


if __name__ == "__main__":
    build()
