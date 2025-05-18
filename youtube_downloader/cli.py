"""
Command-line interface module for YouTube Music Downloader.

This module provides the command-line interface and entry points
for the YouTube Music Downloader application.
"""

import sys
import os
from youtube_downloader.app import YouTubeMusicDownloaderApp

def run_cli():
    """Run the command-line interface application.
    
    This function serves as the main entry point for the CLI application.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    app = YouTubeMusicDownloaderApp()
    return app.run()

def main():
    """Main entry point function for console scripts.
    
    This function is designed to be an entry point in setup.py.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        return run_cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 