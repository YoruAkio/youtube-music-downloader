"""
File management utilities for YouTube Music Downloader.
"""

import os
import re
import shutil
import glob
import logging
from pathlib import Path
from functools import lru_cache

# Create a module-level logger
logger = logging.getLogger("youtube_downloader.file_utils")

class FileManager:
    """
    Manage file operations for the YouTube Music Downloader.
    
    This class handles operations like creating directories, cleaning up
    temporary files, and checking if files exist.
    """
    
    def __init__(self, output_dir="downloads", temp_dir="temp_downloads", logger=None, verbose=False):
        """
        Initialize the file manager.
        
        Args:
            output_dir: Directory to save downloaded files
            temp_dir: Directory for temporary files during download/conversion
            logger: Logger instance to use (optional)
            verbose: Whether verbose logging is enabled
        """
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.logger = logger or logging.getLogger("youtube_downloader.file_utils")
        self.verbose = verbose
        
        self.logger.debug(f"FileManager initialized with output_dir={output_dir}, temp_dir={temp_dir}")
        self.ensure_directories()
        self._file_cache = {}
        self._cache_initialized = False
    
    def ensure_directories(self):
        """Create the output and temporary directories if they don't exist."""
        self.logger.debug(f"Ensuring directories exist: {self.output_dir}, {self.temp_dir}")
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
    
    def _initialize_file_cache(self):
        """Build a cache of existing files for faster lookup."""
        if not os.path.exists(self.output_dir) or self._cache_initialized:
            self.logger.debug("File cache already initialized or output directory doesn't exist")
            return
        
        self.logger.debug("Initializing file cache")
        
        # Clear existing cache
        self._file_cache = {}
        
        # Scan the directory once and build a cache of lowercase filenames
        file_count = 0
        for file in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                file_base = os.path.splitext(file)[0].lower()
                file_ext = os.path.splitext(file)[1].lower()
                
                # Store both the base name and full filename
                if file_base not in self._file_cache:
                    self._file_cache[file_base] = []
                self._file_cache[file_base].append((file, file_ext, file_path))
                file_count += 1
                
                if self.verbose:
                    self.logger.debug(f"Added to cache: {file}")
        
        self._cache_initialized = True
        self.logger.debug(f"File cache initialized with {file_count} files")
    
    def file_exists(self, title, extension=None):
        """
        Check if a file with the given title exists in the output directory.
        Uses a cached approach for better performance when checking multiple files.
        
        Args:
            title: Title to check for
            extension: Optional file extension to check for
            
        Returns:
            str or False: Path to the file if it exists, False otherwise
        """
        self.logger.debug(f"Checking if file exists: '{title}'{f' with extension .{extension}' if extension else ''}")
        
        if not os.path.exists(self.output_dir):
            self.logger.debug(f"Output directory does not exist: {self.output_dir}")
            return False
            
        # Initialize the cache if needed
        if not self._cache_initialized:
            self.logger.debug("File cache not initialized, initializing now")
            self._initialize_file_cache()
        
        # Clean and normalize the title
        clean_title = self.clean_filename(title).lower()
        if self.verbose:
            self.logger.debug(f"Cleaned title: '{clean_title}'")
        
        # Check if the title is in our cache
        if clean_title in self._file_cache:
            matching_files = self._file_cache[clean_title]
            self.logger.debug(f"Found {len(matching_files)} potential matches in cache")
            
            # If extension is specified, find matching extension
            if extension:
                ext = f".{extension.lower()}"
                for _, file_ext, file_path in matching_files:
                    if file_ext.lower() == ext:
                        self.logger.debug(f"Found matching file with extension {ext}: {file_path}")
                        return file_path
                self.logger.debug(f"No matching file with extension {ext} found")
            # Otherwise return the first match
            elif matching_files:
                file_path = matching_files[0][2]  # Return the path
                self.logger.debug(f"Found matching file: {file_path}")
                return file_path
        else:
            self.logger.debug(f"No matching files found for '{clean_title}'")
        
        return False
    
    def invalidate_cache(self):
        """Invalidate the file cache to force a refresh on next check."""
        self.logger.debug("Invalidating file cache")
        self._cache_initialized = False
    
    def move_file(self, source, destination=None):
        """
        Move a file to the destination, or to the output directory if no destination is specified.
        
        Args:
            source: Path to the source file
            destination: Optional destination path
            
        Returns:
            str: Path to the destination file
        """
        self.logger.debug(f"Moving file from: {source}")
        
        if not destination:
            destination = os.path.join(self.output_dir, os.path.basename(source))
            self.logger.debug(f"No destination specified, using: {destination}")
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            self.logger.debug(f"Creating destination directory: {dest_dir}")
            os.makedirs(dest_dir, exist_ok=True)
        
        # Remove destination file if it exists
        if os.path.exists(destination):
            self.logger.debug(f"Destination file already exists, removing: {destination}")
            os.remove(destination)
        
        # Move the file
        self.logger.debug(f"Renaming file from {source} to {destination}")
        os.rename(source, destination)
        
        # Invalidate cache since we've modified files
        self.invalidate_cache()
        
        return destination
    
    def cleanup_temp_directory(self):
        """Clean up all files in the temporary directory."""
        self.logger.debug(f"Cleaning up temporary directory: {self.temp_dir}")
        
        if os.path.exists(self.temp_dir):
            file_count = 0
            error_count = 0
            
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        if self.verbose:
                            self.logger.debug(f"Removing temporary file: {file_path}")
                        os.remove(file_path)
                        file_count += 1
                except Exception as e:
                    error_count += 1
                    self.logger.warning(f"Error removing temporary file {file_path}: {str(e)}")
            
            self.logger.debug(f"Removed {file_count} temporary files, {error_count} errors")
            
            try:
                # Try to remove the directory itself
                self.logger.debug(f"Removing temporary directory: {self.temp_dir}")
                os.rmdir(self.temp_dir)
            except Exception as e:
                self.logger.warning(f"Could not remove temporary directory: {str(e)}") 