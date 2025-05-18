#!/usr/bin/env python3

"""
YouTube Music Downloader - A command-line tool to download YouTube videos or playlists.

This is the main entry point for the application.
"""

import sys
import os
import logging

# Create a simple logger for startup debugging
logger = logging.getLogger("youtube_downloader.main")

# Add path handling to ensure modules are found when frozen with PyInstaller
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running as a PyInstaller bundle
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
    # Fix working directory for frozen app
    os.chdir(base_path)
    logger.debug(f"Running as frozen application. MEIPASS: {base_path}")
else:
    # Running in a normal Python environment
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    logger.debug(f"Running in normal Python environment. Script dir: {script_dir}")
    
    # Change to the script's directory to ensure we can find other resources
    if os.getcwd() != script_dir:
        logger.debug(f"Changing directory from {os.getcwd()} to {script_dir}")
        os.chdir(script_dir)

# Import needs to be after path adjustments
from youtube_downloader.cli import main

if __name__ == "__main__":
    sys.exit(main())