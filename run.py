#!/usr/bin/env python3
"""
Insurance Master Launcher

Simple launcher script for the Insurance Master application.
This script ensures proper Python path setup and launches the main application.
"""

import sys
import os
from pathlib import Path

def main():
    """Launch the Insurance Master application"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Add src directory to Python path
    src_dir = script_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    else:
        print("Error: src directory not found!")
        print(f"Expected location: {src_dir}")
        sys.exit(1)
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Import and run the main application
    try:
        from src.main import main as run_app
        run_app()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
