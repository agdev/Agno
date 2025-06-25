"""
Financial Assistant - Main Entry Point

This file provides the main entry point for the Financial Assistant application.
It imports and runs the Streamlit application from the src directory.
"""

import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def main():
    """Main entry point - runs the Streamlit application"""
    from src.main import main as streamlit_main
    streamlit_main()

if __name__ == "__main__":
    main()
