"""
File management utilities for YouTube Music Downloader.
"""

import os
import re
import shutil
from pathlib import Path

class FileManager:
    """
    Manage file operations for the YouTube Music Downloader.
    
    This class handles operations like creating directories, cleaning up
    temporary files, and checking if files exist.
    """
    
    def __init__(self, output_dir="downloads", temp_dir="temp_downloads"):
        """
        Initialize the file manager.
        
        Args:
            output_dir: Directory to save downloaded files
            temp_dir: Directory for temporary files during download/conversion
        """
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create the output and temporary directories if they don't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def clean_filename(self, filename):
        """
        Clean a string to be usable as a filename.
        
        Args:
            filename: String to clean
            
        Returns:
            clean_filename: Filename safe string
        """
        # Remove invalid file characters
        return re.sub(r'[\\/*?:"<>|]', "", filename)
    
    def file_exists(self, title, extension=None):
        """
        Check if a file with the given title exists in the output directory.
        
        Args:
            title: Title to check for
            extension: Optional file extension to check for
            
        Returns:
            str or False: Path to the file if it exists, False otherwise
        """
        if not os.path.exists(self.output_dir):
            return False
        
        # Clean title to create a filename-safe string
        clean_title = self.clean_filename(title)
        
        for file in os.listdir(self.output_dir):
            file_base = os.path.splitext(file)[0]
            if clean_title.lower() == file_base.lower():
                file_path = os.path.join(self.output_dir, file)
                # Make sure it's a file and not a directory
                if os.path.isfile(file_path):
                    # If extension is specified, check that it matches
                    if extension:
                        if file.lower().endswith(f".{extension.lower()}"):
                            return file_path
                    else:
                        return file_path
        
        return False
    
    def move_file(self, source, destination=None):
        """
        Move a file to the destination, or to the output directory if no destination is specified.
        
        Args:
            source: Path to the source file
            destination: Optional destination path
            
        Returns:
            str: Path to the destination file
        """
        if not destination:
            destination = os.path.join(self.output_dir, os.path.basename(source))
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        # Remove destination file if it exists
        if os.path.exists(destination):
            os.remove(destination)
        
        # Move the file
        os.rename(source, destination)
        return destination
    
    def cleanup_temp_directory(self):
        """Clean up all files in the temporary directory."""
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass  # Ignore errors during cleanup
            
            try:
                # Try to remove the directory itself
                os.rmdir(self.temp_dir)
            except Exception:
                pass  # Ignore errors during cleanup 