#!/usr/bin/env python3
"""
Financial Assistant - Application Entry Point

This script serves as the main entry point for the Financial Assistant application.
Run this script to start the Streamlit web application.

Usage:
    python run.py
    or
    streamlit run src/main.py
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for the Financial Assistant application"""
    
    # Add src directory to Python path
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    
    # Change to src directory for proper imports
    os.chdir(src_path)
    
    try:
        # Import and run the Streamlit application
        from main import main as streamlit_main
        streamlit_main()
    except ImportError as e:
        print(f"Error importing the application: {e}")
        print("Make sure all dependencies are installed.")
        print("Run: uv sync  # to install dependencies")
        sys.exit(1)
    except Exception as e:
        print(f"Error running the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()