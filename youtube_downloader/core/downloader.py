"""
YouTube downloader module for downloading videos and playlists.
"""

import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

import yt_dlp

from youtube_downloader.utils.file_utils import FileManager
from youtube_downloader.utils.progress import ProgressTracker

# Create module-level logger
logger = logging.getLogger("youtube_downloader.downloader")

# Regular expressions to validate YouTube URLs
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
YOUTUBE_PLAYLIST_REGEX = r'^(https?://)?(www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'

# Quality settings
QUALITY_SETTINGS = {
    'low': {'audio': '128k', 'video': '360p'},
    'medium': {'audio': '192k', 'video': '480p'},
    'high': {'audio': '320k', 'video': '720p'}
}

@dataclass
class DownloadResult:
    """Class to store download result information."""
    url: str
    status: str = 'pending'  # 'pending', 'success', 'error', 'skipped'
    file_path: str = ""
    title: str = ""
    error: str = ""

class YouTubeDownloader:
    """
    Class for downloading YouTube videos and playlists.
    
    This class handles validating URLs, getting video information,
    and downloading videos from YouTube.
    """
    
    def __init__(self, file_manager=None, progress_tracker=None, logger=None, verbose=False):
        """
        Initialize the YouTube downloader.
        
        Args:
            file_manager: FileManager instance or None to create a new one
            progress_tracker: ProgressTracker instance or None to create a new one
            logger: Optional logger instance
            verbose: Whether verbose logging is enabled
        """
        self.file_manager = file_manager or FileManager()
        self.progress_tracker = progress_tracker
        self.logger = logger or logging.getLogger("youtube_downloader.downloader")
        self.verbose = verbose
        
        self.logger.debug("YouTubeDownloader initialized")
        
    def validate_url(self, url):
        """
        Validate if the provided URL is a valid YouTube video or playlist URL.
        
        Args:
            url: URL to validate
            
        Returns:
            str or None: 'video', 'playlist', or None if invalid
        """
        self.logger.debug(f"Validating URL: {url}")
        
        if re.match(YOUTUBE_VIDEO_REGEX, url):
            self.logger.debug(f"URL is a valid YouTube video: {url}")
            return 'video'
        elif re.match(YOUTUBE_PLAYLIST_REGEX, url):
            self.logger.debug(f"URL is a valid YouTube playlist: {url}")
            return 'playlist'
        else:
            self.logger.debug(f"URL is not a valid YouTube video or playlist: {url}")
            return None
    
    def get_video_info(self, url):
        """
        Get information about a YouTube video.
        
        Args:
            url: URL of the video
            
        Returns:
            dict or None: Video information or None if error
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception as e:
                print(f"Error getting video info: {e}")
                return None
    
    def get_playlist_videos(self, url):
        """
        Get all video URLs from a YouTube playlist.
        
        Args:
            url: URL of the playlist
            
        Returns:
            list: List of video URLs
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    video_urls = []
                    for entry in info['entries']:
                        if entry.get('url'):
                            video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
                    return video_urls
                return []
            except Exception as e:
                print(f"Error getting playlist info: {e}")
                return []
    
    def download_video(self, url, output_format='mp3', quality='medium', 
                      is_video=False, task_id=None):
        """
        Download a single video.
        
        Args:
            url: URL of the video
            output_format: Audio format (ignored if is_video is True)
            quality: Quality setting ('low', 'medium', 'high')
            is_video: Whether to download as video
            task_id: Task ID for progress tracking
            
        Returns:
            DownloadResult: Result of the download operation
        """
        result = DownloadResult(url=url)
        output_template = '%(title)s.%(ext)s'
        
        # Get quality settings
        video_quality = QUALITY_SETTINGS[quality]['video']
        audio_quality = QUALITY_SETTINGS[quality]['audio']
        
        try:
            if is_video:
                # Video download options
                format_spec = f'bestvideo[height<={video_quality[:-1]}]+bestaudio/best[height<={video_quality[:-1]}]'
                ydl_opts = {
                    'format': format_spec,
                    'outtmpl': f'{self.file_manager.temp_dir}/{output_template}',
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4',
                }
            else:
                # Audio download options
                format_str = 'bestaudio/best'
                
                ydl_opts = {
                    'format': format_str,
                    'outtmpl': f'{self.file_manager.temp_dir}/{output_template}',
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': output_format,
                        'preferredquality': audio_quality.replace('k', ''),
                    }],
                }
            
            # Add progress hook if tracker is available
            if self.progress_tracker and task_id is not None:
                ydl_opts['progress_hooks'] = [
                    lambda d: self.progress_tracker.update_progress(d, task_id)
                ]
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                # Handle extensions for audio downloads
                if not is_video:
                    base, _ = os.path.splitext(file_path)
                    file_path = f"{base}.{output_format}"
                
                # Check if the file exists in the temp directory
                if os.path.exists(file_path):
                    # Move to the output directory
                    dest_path = self.file_manager.move_file(file_path)
                else:
                    # Sometimes yt-dlp adds the audio extension automatically
                    temp_path = f"{self.file_manager.temp_dir}/{info['title']}.{output_format}"
                    if os.path.exists(temp_path):
                        dest_path = self.file_manager.move_file(temp_path)
                    else:
                        raise FileNotFoundError(f"Downloaded file not found: {file_path}")
                
                # Mark task as complete if progress tracker is available
                if self.progress_tracker and task_id is not None:
                    self.progress_tracker.complete_task(task_id)
                
                # Set success result
                result.status = 'success'
                result.file_path = dest_path
                result.title = info['title']
                
            return result
        except Exception as e:
            result.status = 'error'
            result.error = str(e)
            return result
    
    def process_url(self, url, output_format='mp3', quality='medium', is_video=False, 
                   force=False, parallel=3):
        """
        Process a URL (video or playlist) by downloading its content.
        
        Args:
            url: URL to process
            output_format: Audio format (ignored if is_video is True)
            quality: Quality setting ('low', 'medium', 'high')
            is_video: Whether to download as video
            force: Whether to force download even if file exists
            parallel: Number of parallel downloads (0 for sequential)
            
        Returns:
            list: List of DownloadResult instances
        """
        url_type = self.validate_url(url)
        
        if url_type == 'video':
            return self._process_single_video(url, output_format, quality, is_video, force)
        elif url_type == 'playlist':
            return self._process_playlist(url, output_format, quality, is_video, force, parallel)
        else:
            print(f"Invalid URL: {url}")
            return []
    
    def _process_single_video(self, url, output_format, quality, is_video, force):
        """Process a single video URL."""
        # Get video info
        info = self.get_video_info(url)
        if not info:
            print(f"Could not retrieve info for {url}")
            return [DownloadResult(url=url, status='error', error="Could not retrieve video info")]
        
        title = info.get('title', 'Unknown Title')
        
        # Check if file already exists
        extension = 'mp4' if is_video else output_format
        existing_file = self.file_manager.file_exists(title, extension)
        
        if existing_file and not force:
            print(f"Skipping download: '{title}' already exists as '{os.path.basename(existing_file)}'")
            return [DownloadResult(
                url=url, 
                status='skipped', 
                file_path=existing_file, 
                title=title
            )]
        
        # Create progress task if tracker is available
        task_id = None
        if self.progress_tracker:
            task_id = self.progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
        
        # Download the video
        result = self.download_video(url, output_format, quality, is_video, task_id)
        return [result]
    
    def _process_playlist(self, url, output_format, quality, is_video, force, parallel):
        """Process a playlist URL."""
        # Get playlist videos
        video_urls = self.get_playlist_videos(url)
        if not video_urls:
            print(f"No videos found in playlist: {url}")
            return []
        
        print(f"Found {len(video_urls)} videos in playlist")
        results = []
        
        # Check which videos already exist if not forcing download
        if not force:
            print("Checking for existing files...")
            existing_count = 0
            videos_to_download = []
            
            for video_url in video_urls:
                info = self.get_video_info(video_url)
                if info:
                    title = info.get('title', 'Unknown Title')
                    extension = 'mp4' if is_video else output_format
                    existing_file = self.file_manager.file_exists(title, extension)
                    
                    if existing_file:
                        existing_count += 1
                        results.append(DownloadResult(
                            url=video_url, 
                            status='skipped', 
                            file_path=existing_file, 
                            title=title
                        ))
                    else:
                        videos_to_download.append((video_url, info))
                else:
                    # If we can't get info, still try to download
                    videos_to_download.append((video_url, None))
            
            if existing_count > 0:
                print(f"Skipping {existing_count} videos that already exist")
            
            # Keep only videos that need to be downloaded
            video_urls_with_info = videos_to_download
        else:
            # Get info for all videos
            video_urls_with_info = [(url, self.get_video_info(url)) for url in video_urls]
        
        # Skip if all videos exist
        if not video_urls_with_info:
            print("All videos in playlist already exist. Nothing to download.")
            return results
        
        print(f"Downloading {len(video_urls_with_info)} videos...")
        
        # Sequential or parallel processing
        if parallel <= 0:  # Sequential
            for idx, (video_url, info) in enumerate(video_urls_with_info, 1):
                title = info.get('title', 'Unknown Title') if info else f"Video {idx}"
                print(f"Processing video {idx}/{len(video_urls_with_info)}: {title}")
                
                task_id = None
                if self.progress_tracker:
                    task_id = self.progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                
                result = self.download_video(video_url, output_format, quality, is_video, task_id)
                results.append(result)
        else:  # Parallel
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = []
                
                # Submit all download jobs
                for video_url, info in video_urls_with_info:
                    title = info.get('title', 'Unknown Title') if info else "Unknown Video"
                    
                    task_id = None
                    if self.progress_tracker:
                        task_id = self.progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                    
                    future = executor.submit(
                        self.download_video, 
                        video_url, 
                        output_format, 
                        quality, 
                        is_video, 
                        task_id
                    )
                    futures.append(future)
                
                # Process results as they complete
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
        
        return results 