"""
Progress tracking utilities for YouTube Music Downloader.
"""

import os
import logging
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    BarColumn, 
    TextColumn, 
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.console import Console

# Create module-level logger
logger = logging.getLogger("youtube_downloader.progress")

class ProgressTracker:
    """
    Track and manage progress of multiple tasks with limited visible tasks.
    
    This class helps manage the visibility of progress bars, ensuring that
    only a limited number are shown at once for better readability.
    """
    
    def __init__(self, progress=None, max_visible=3, console=None, logger=None, verbose=False):
        """
        Initialize the progress tracker.
        
        Args:
            progress: An existing Progress instance or None to create a new one
            max_visible: Maximum number of tasks to show at once
            console: Console instance for output
            logger: Optional logger instance
            verbose: Whether verbose logging is enabled
        """
        self.console = console or Console()
        self.progress = progress
        self.max_visible = max_visible
        self.active_tasks = []
        self.logger = logger or logging.getLogger("youtube_downloader.progress")
        self.verbose = verbose
        
        self.logger.debug(f"ProgressTracker initialized with max_visible={max_visible}")
        
    def create_progress(self):
        """Create and return a new Progress instance."""
        self.logger.debug("Creating new Progress instance")
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
            refresh_per_second=10
        )
        return self.progress
    
    def add_task(self, description, total=100):
        """
        Add a task to the progress tracker.
        
        Args:
            description: Description of the task
            total: Total steps for the task
            
        Returns:
            task_id: ID of the created task
        """
        self.logger.debug(f"Adding new task: {description}")
        
        if not self.progress:
            self.logger.error("Progress instance not initialized. Call create_progress() first.")
            raise ValueError("Progress instance not initialized. Call create_progress() first.")
            
        # Create task, but only make it visible if we have room
        visible = len(self.active_tasks) < self.max_visible
        task_id = self.progress.add_task(description, total=total, visible=visible)
        self.active_tasks.append(task_id)
        
        self.logger.debug(f"Created task ID {task_id}, visible: {visible}")
        return task_id
        
    def complete_task(self, task_id):
        """
        Mark a task as complete and potentially make a hidden task visible.
        
        Args:
            task_id: ID of the task to complete
        """
        self.logger.debug(f"Completing task ID {task_id}")
        
        if not self.progress:
            self.logger.warning("Cannot complete task: Progress instance not initialized")
            return
            
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
            self.logger.debug(f"Removed task ID {task_id} from active tasks")
            
            # Make a hidden task visible if there's room now
            for t_id in self.progress.task_ids:
                if t_id not in self.active_tasks and not self.progress.tasks[t_id].visible:
                    self.progress.update(t_id, visible=True)
                    self.active_tasks.append(t_id)
                    self.logger.debug(f"Made task ID {t_id} visible")
                    break
    
    def update_progress(self, download_data, task_id):
        """
        Update progress based on download data from yt-dlp.
        
        Args:
            download_data: Download data from yt-dlp progress hook
            task_id: ID of the task to update
        """
        if not self.progress or task_id is None:
            return
        
        if self.verbose:
            self.logger.debug(f"Update progress for task ID {task_id}: {download_data['status']}")
            
        if download_data['status'] == 'downloading':
            try:
                # Try to get percentage from _percent_str first
                if '_percent_str' in download_data:
                    percent = float(download_data['_percent_str'].strip('%'))
                    if self.verbose:
                        self.logger.debug(f"Progress from _percent_str: {percent}%")
                # Fall back to calculating percentage from downloaded_bytes and total_bytes
                elif 'downloaded_bytes' in download_data and 'total_bytes' in download_data and download_data['total_bytes'] > 0:
                    percent = (download_data['downloaded_bytes'] / download_data['total_bytes']) * 100
                    if self.verbose:
                        self.logger.debug(f"Progress calculated from bytes: {percent:.1f}% ({download_data['downloaded_bytes']}/{download_data['total_bytes']})")
                # Try total_bytes_estimate if total_bytes is not available
                elif 'downloaded_bytes' in download_data and 'total_bytes_estimate' in download_data and download_data['total_bytes_estimate'] > 0:
                    percent = (download_data['downloaded_bytes'] / download_data['total_bytes_estimate']) * 100
                    if self.verbose:
                        self.logger.debug(f"Progress calculated from estimate: {percent:.1f}% ({download_data['downloaded_bytes']}/{download_data['total_bytes_estimate']})")
                else:
                    # If no reliable percentage data, just pulse the progress bar
                    self.logger.debug("No percentage data available, pulsing progress bar")
                    self.progress.update(task_id, advance=0.5)
                    return
                
                # Get speed info if available
                speed_info = f" ({download_data['_speed_str']})" if '_speed_str' in download_data else ""
                
                # Get clean filename for better display
                filename = os.path.basename(download_data['filename'].split('/')[-1])
                
                # Update the progress bar with better formatting
                self.progress.update(
                    task_id, 
                    completed=percent, 
                    description=f"[cyan]Downloading: {filename}{speed_info}[/cyan]"
                )
            except Exception as e:
                # In case of any error, just pulse the progress bar
                self.logger.warning(f"Error updating progress: {str(e)}")
                self.progress.update(task_id, advance=0.5)

