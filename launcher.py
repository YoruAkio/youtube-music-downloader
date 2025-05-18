#!/usr/bin/env python3

"""
Launcher script for YouTube Music Downloader.
Simply forwards all arguments to main.py
"""

import sys
import os

# Get the absolute path to main.py
script_dir = os.path.dirname(os.path.abspath(__file__))
main_script = os.path.join(script_dir, "main.py")

# Run the main.py script with all arguments passed to this script
os.execv(sys.executable, [sys.executable, main_script] + sys.argv[1:]) 