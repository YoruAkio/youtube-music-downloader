"""
Audio converter module for converting video/audio files to different formats.
"""

import os
import re
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from youtube_downloader.core.downloader import DownloadResult, QUALITY_SETTINGS
from youtube_downloader.utils.file_utils import FileManager

# Create module-level logger
logger = logging.getLogger("youtube_downloader.converter")

class AudioConverter:
    """
    Class for converting downloaded files to different formats.
    
    This class handles the conversion of downloaded files to different 
    audio formats using FFmpeg.
    """
    
    def __init__(self, file_manager=None, progress_tracker=None, logger=None, verbose=False):
        """
        Initialize the audio converter.
        
        Args:
            file_manager: FileManager instance or None to create a new one
            progress_tracker: ProgressTracker instance or None
            logger: Optional logger instance
            verbose: Whether verbose logging is enabled
        """
        self.file_manager = file_manager or FileManager()
        self.progress_tracker = progress_tracker
        self.logger = logger or logging.getLogger("youtube_downloader.converter")
        self.verbose = verbose
        
        # Regex patterns for parsing FFmpeg output
        self.duration_regex = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})")
        self.time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        self.logger.debug("AudioConverter initialized")
    
    def convert_file(self, result, output_format, quality, task_id=None):
        """
        Convert a downloaded file to the desired format.
        
        Args:
            result: DownloadResult instance to convert
            output_format: Desired output format
            quality: Quality setting ('low', 'medium', 'high')
            task_id: Task ID for progress tracking
            
        Returns:
            DownloadResult: Updated DownloadResult instance
        """
        # Skip if not needed
        if result.status != 'success':
            return result
        
        input_file = result.file_path
        if not input_file or not os.path.exists(input_file):
            result.status = 'error'
            result.error = "Input file does not exist"
            return result
        
        # Check if conversion is needed
        base, ext = os.path.splitext(input_file)
        current_ext = ext[1:] if ext else ""
        
        # If file is already in the correct format, skip conversion
        if current_ext.lower() == output_format.lower():
            return result
        
        # Prepare output file path
        output_file = f"{base}.{output_format}"
        
        # Update progress if available
        if self.progress_tracker and task_id is not None:
            basename = os.path.basename(input_file)
            self.progress_tracker.progress.update(
                task_id, 
                description=f"[yellow]Converting: {basename}[/yellow]"
            )
        
        try:
            # Get audio quality setting
            quality_value = QUALITY_SETTINGS[quality]['audio']
            
            # Prepare FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-b:a', quality_value,
                '-f', output_format,
                '-y',  # Overwrite output files
                output_file
            ]
            
            # Run the FFmpeg process and monitor its progress
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                universal_newlines=True
            )
            
            # Parse FFmpeg output for progress
            total_duration_seconds = None
            
            # Poll process output
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Try to get the total duration
                    if total_duration_seconds is None:
                        duration_match = self.duration_regex.search(output)
                        if duration_match:
                            h, m, s = map(float, duration_match.groups())
                            total_duration_seconds = h * 3600 + m * 60 + s
                    
                    # Try to get the current progress
                    if self.progress_tracker and task_id is not None and total_duration_seconds:
                        time_match = self.time_regex.search(output)
                        if time_match:
                            h, m, s = map(float, time_match.groups())
                            current_seconds = h * 3600 + m * 60 + s
                            percent = min(100, (current_seconds / total_duration_seconds) * 100)
                            self.progress_tracker.progress.update(task_id, completed=percent)
            
            # Process any remaining output
            process.communicate()
            
            # Check if process was successful
            if process.returncode != 0:
                raise Exception(f"FFmpeg conversion failed with return code {process.returncode}")
            
            # Remove the original file
            os.remove(input_file)
            
            # Update the result
            result.file_path = output_file
            
            # Mark task as complete if progress tracker is available
            if self.progress_tracker and task_id is not None:
                self.progress_tracker.complete_task(task_id)
                basename = os.path.basename(output_file)
                self.progress_tracker.progress.update(
                    task_id, 
                    completed=100, 
                    description=f"[green]Converted: {basename}[/green]"
                )
            
            return result
        except Exception as e:
            # Update progress on error
            if self.progress_tracker and task_id is not None:
                self.progress_tracker.progress.update(
                    task_id, 
                    description=f"[red]Conversion failed: {str(e)}[/red]"
                )
            
            # Update result on error
            result.status = 'error'
            result.error = f"Conversion error: {str(e)}"
            return result
    
    def batch_convert(self, results, output_format, quality, parallel=1):
        """
        Convert a batch of downloaded files.
        
        Args:
            results: List of DownloadResult instances
            output_format: Desired output format
            quality: Quality setting ('low', 'medium', 'high')
            parallel: Number of parallel conversions (0 for sequential)
            
        Returns:
            list: Updated list of DownloadResult instances
        """
        # Filter successful downloads
        successful_downloads = [r for r in results if r.status == 'success']
        other_downloads = [r for r in results if r.status != 'success']
        
        if not successful_downloads:
            return results
        
        print(f"Processing {len(successful_downloads)} audio conversions...")
        converted_results = []
        
        # Sequential or parallel processing
        if parallel <= 0:  # Sequential
            for idx, result in enumerate(successful_downloads, 1):
                basename = os.path.basename(result.file_path)
                
                task_id = None
                if self.progress_tracker:
                    task_id = self.progress_tracker.add_task(
                        f"[yellow]Converting: {basename}[/yellow]", 
                        total=100
                    )
                
                converted_result = self.convert_file(result, output_format, quality, task_id)
                converted_results.append(converted_result)
        else:  # Parallel
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = []
                
                # Submit all conversion jobs
                for result in successful_downloads:
                    basename = os.path.basename(result.file_path)
                    
                    task_id = None
                    if self.progress_tracker:
                        task_id = self.progress_tracker.add_task(
                            f"[yellow]Converting: {basename}[/yellow]", 
                            total=100
                        )
                    
                    future = executor.submit(self.convert_file, result, output_format, quality, task_id)
                    futures.append(future)
                
                # Process results as they complete
                for future in as_completed(futures):
                    converted_result = future.result()
                    converted_results.append(converted_result)
        
        return converted_results + other_downloads 