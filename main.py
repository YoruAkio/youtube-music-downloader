#!/usr/bin/env python3

"""
YouTube Music Downloader - A command-line tool to download YouTube videos or playlists.

This is the main entry point for the application.
"""

__version__ = "1.0.0"

import sys
import time
import os
import re
import argparse
import subprocess
import ssl
import certifi
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Callable, Union
from urllib.parse import urlparse, parse_qs

# Fix SSL certificate verification for compiled executables
def fix_ssl_certificates():
    try:
        # Check if we're in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # We are running in a PyInstaller bundle
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
            
            # Create a default SSL context with the certifi certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl._create_default_https_context = lambda: ssl_context
            
            print("SSL certificates configured for compiled executable")
    except Exception as e:
        print(f"Warning: Could not configure SSL certificates: {str(e)}")

# Call this function early
fix_ssl_certificates()

import yt_dlp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

# Import our package classes
from youtube_downloader import __version__
from youtube_downloader.utils.progress import ProgressTracker
from youtube_downloader.utils.file_utils import FileManager
from youtube_downloader.core.downloader import YouTubeDownloader
from youtube_downloader.core.converter import AudioConverter

# Initialize Rich console for pretty output
console = Console()

# Regular expressions to validate YouTube URLs
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
YOUTUBE_PLAYLIST_REGEX = r'^(https?://)?(www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'

# Quality settings
QUALITY_SETTINGS = {
    'low': {'audio': '128k', 'video': '360p'},
    'medium': {'audio': '192k', 'video': '480p'},
    'high': {'audio': '320k', 'video': '720p'}
}

def validate_url(url):
    """Validate if the provided URL is a valid YouTube video or playlist URL."""
    if re.match(YOUTUBE_VIDEO_REGEX, url):
        return 'video'
    elif re.match(YOUTUBE_PLAYLIST_REGEX, url):
        return 'playlist'
    else:
        return None

def get_video_info(url):
    """Get information about a YouTube video."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            console.print(f"[bold red]Error getting video info: {e}[/bold red]")
            return None

def get_playlist_videos(url):
    """Get all video URLs from a YouTube playlist."""
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
            console.print(f"[bold red]Error getting playlist info: {e}[/bold red]")
            return []

def download_video(video_url, args, progress=None, task_id=None, progress_tracker=None):
    """Download a single video."""
    output_template = '%(title)s.%(ext)s'
    temp_dir = 'temp_downloads'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Prepare options based on quality and format
    quality = args.quality
    video_quality = QUALITY_SETTINGS[quality]['video']
    audio_quality = QUALITY_SETTINGS[quality]['audio']
    
    if args.video:
        # Video download options
        format_spec = f'bestvideo[height<={video_quality[:-1]}]+bestaudio/best[height<={video_quality[:-1]}]'
        ydl_opts = {
            'format': format_spec,
            'outtmpl': f'{temp_dir}/{output_template}',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: update_progress(d, progress, task_id)],
            'merge_output_format': 'mp4',
        }
    else:
        # Audio download options
        format_str = 'bestaudio/best'
        audio_format = args.format
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': f'{temp_dir}/{output_template}',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: update_progress(d, progress, task_id)],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': audio_quality.replace('k', ''),
            }],
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Handle extensions
            if not args.video:
                base, _ = os.path.splitext(file_path)
                file_path = f"{base}.{args.format}"
            
            # Move the file to the destination directory
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir, exist_ok=True)
            
            dest_path = os.path.join(args.output_dir, os.path.basename(file_path))
            if os.path.exists(file_path):
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(file_path, dest_path)
            else:
                # Sometimes yt-dlp adds the audio extension automatically
                temp_path = f"{temp_dir}/{info['title']}.{args.format}"
                if os.path.exists(temp_path):
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.rename(temp_path, dest_path)
            
            # Mark task as complete for progress tracking
            if progress_tracker and task_id:
                progress_tracker.complete_task(task_id)
            
            if progress and task_id:
                progress.update(task_id, completed=100, description=f"[green]Completed: {info['title']}[/green]")
                
            return {'url': video_url, 'status': 'success', 'file': dest_path, 'title': info['title']}
    except Exception as e:
        if progress and task_id:
            progress.update(task_id, description=f"[red]Failed: Download error[/red]")
        return {'url': video_url, 'status': 'error', 'error': str(e)}

def update_progress(d, progress, task_id):
    """Update download progress."""
    if progress and task_id:
        if d['status'] == 'downloading':
            try:
                # Try to get percentage from _percent_str first
                if '_percent_str' in d:
                    percent = float(d['_percent_str'].strip('%'))
                # Fall back to calculating percentage from downloaded_bytes and total_bytes
                elif 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes'] > 0:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                # Try total_bytes_estimate if total_bytes is not available
                elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    # If no reliable percentage data, just pulse the progress bar
                    progress.update(task_id, advance=0.5)
                    return
                
                # Get speed info if available
                speed_info = f" ({d['_speed_str']})" if '_speed_str' in d else ""
                
                # Get clean filename for better display
                filename = os.path.basename(d['filename'].split('/')[-1])
                
                # Update the progress bar with better formatting
                progress.update(
                    task_id, 
                    completed=percent, 
                    description=f"[cyan]Downloading: {filename}{speed_info}[/cyan]"
                )
            except Exception:
                # In case of any error, just pulse the progress bar
                progress.update(task_id, advance=0.5)

def file_exists_in_output_dir(title, args):
    """Check if a file with similar name already exists in the output directory."""
    if not os.path.exists(args.output_dir):
        return False
    
    # Clean title to create a filename-safe string
    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
    
    # Check for existence of file with any supported extension
    extensions = ['mp4'] if args.video else [args.format]
    
    for file in os.listdir(args.output_dir):
        file_base = os.path.splitext(file)[0]
        if clean_title.lower() == file_base.lower():
            file_path = os.path.join(args.output_dir, file)
            # Make sure it's a file and not a directory
            if os.path.isfile(file_path):
                return file_path
    
    return False

def process_url(url, args, progress=None, progress_tracker=None):
    """Process a single URL (video or playlist)."""
    url_type = validate_url(url)
    
    if url_type == 'video':
        info = get_video_info(url)
        if not info:
            console.print(f"[bold red]Could not retrieve info for {url}[/bold red]")
            return []
        
        title = info.get('title', 'Unknown Title')
        
        # Check if file already exists
        existing_file = file_exists_in_output_dir(title, args)
        if existing_file and not args.force:
            console.print(f"[yellow]Skipping download: '{title}' already exists as '{os.path.basename(existing_file)}'[/yellow]")
            return [{'url': url, 'status': 'skipped', 'file': existing_file, 'title': title}]
        
        task_id = None
        if progress and progress_tracker:
            task_id = progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
        elif progress:
            task_id = progress.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100, completed=0)
        
        result = download_video(url, args, progress, task_id, progress_tracker)
        return [result]
    
    elif url_type == 'playlist':
        video_urls = get_playlist_videos(url)
        if not video_urls:
            console.print(f"[bold red]No videos found in playlist: {url}[/bold red]")
            return []
        
        console.print(f"[bold cyan]Found {len(video_urls)} videos in playlist[/bold cyan]")
        results = []
        
        # Check which videos already exist
        if not args.force:
            console.print("[cyan]Checking for existing files...[/cyan]")
            existing_count = 0
            videos_to_download = []
            
            for video_url in video_urls:
                info = get_video_info(video_url)
                if info:
                    title = info.get('title', 'Unknown Title')
                    existing_file = file_exists_in_output_dir(title, args)
                    if existing_file:
                        existing_count += 1
                        results.append({'url': video_url, 'status': 'skipped', 'file': existing_file, 'title': title})
                    else:
                        videos_to_download.append((video_url, info))
                else:
                    videos_to_download.append((video_url, None))
            
            if existing_count > 0:
                console.print(f"[yellow]Skipping {existing_count} videos that already exist[/yellow]")
            
            # Keep only videos that need to be downloaded with their info
            video_urls_with_info = videos_to_download
        else:
            # Get info for all videos for better user experience
            video_urls_with_info = [(url, get_video_info(url)) for url in video_urls]
        
        if not video_urls_with_info:
            console.print("[yellow]All videos in playlist already exist. Nothing to download.[/yellow]")
            return results
        
        console.print(f"[bold cyan]Downloading {len(video_urls_with_info)} videos...[/bold cyan]")
        
        # Set up parallel downloads
        max_workers = args.parallel_download
        
        if max_workers == 0:  # If 0, use sequential processing
            for idx, (video_url, info) in enumerate(video_urls_with_info, 1):
                title = info.get('title', 'Unknown Title') if info else f"Video {idx}"
                console.print(f"[bold cyan]Processing video {idx}/{len(video_urls_with_info)}: {title}[/bold cyan]")
                
                task_id = None
                if progress and progress_tracker:
                    task_id = progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                elif progress:
                    task_id = progress.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                
                result = download_video(video_url, args, progress, task_id, progress_tracker)
                results.append(result)
            
        else:  # Parallel processing with better progress tracking
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                # Submit all download jobs
                for video_url, info in video_urls_with_info:
                    title = info.get('title', 'Unknown Title') if info else "Unknown Video"
                    
                    task_id = None
                    if progress and progress_tracker:
                        task_id = progress_tracker.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                    elif progress:
                        task_id = progress.add_task(f"[cyan]Downloading: {title}...[/cyan]", total=100)
                    
                    future = executor.submit(
                        download_video, 
                        video_url, 
                        args, 
                        progress, 
                        task_id,
                        progress_tracker
                    )
                    futures.append(future)
                
                # Process results as they complete
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
        
        return results
    
    else:
        console.print(f"[bold red]Invalid URL: {url}[/bold red]")
        return []

def convert_file(file_info, args, progress=None, task_id=None, progress_tracker=None):
    """Convert a downloaded file to the desired format using ffmpeg."""
    if args.video or file_info['status'] != 'success':
        return file_info  # No conversion needed for videos or failed downloads
    
    try:
        input_file = file_info['file']
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.{args.format}"
        
        # Skip if the file is already in the right format
        if ext[1:] == args.format:
            if progress_tracker and task_id:
                progress_tracker.complete_task(task_id)
            return file_info
        
        # Update progress if available
        if progress and task_id:
            basename = os.path.basename(input_file)
            progress.update(task_id, description=f"[yellow]Converting: {basename}[/yellow]")
        
        # Convert the file with progress monitoring
        quality = QUALITY_SETTINGS[args.quality]['audio']
        
        # Instead of using ffmpeg-python's quiet mode, we'll capture the output
        # and parse it for progress updates
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-b:a', quality,
            '-f', args.format,
            '-y',  # Overwrite output files
            output_file
        ]
        
        # Run the ffmpeg process and monitor its progress
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        
        # Duration regex to extract total duration
        duration_regex = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})")
        # Time regex to extract current progress
        time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        total_duration_seconds = None
        
        # Poll process output
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Try to get the total duration
                if total_duration_seconds is None:
                    duration_match = duration_regex.search(output)
                    if duration_match:
                        h, m, s = map(float, duration_match.groups())
                        total_duration_seconds = h * 3600 + m * 60 + s
                
                # Try to get the current progress
                time_match = time_regex.search(output)
                if time_match and total_duration_seconds and progress and task_id:
                    h, m, s = map(float, time_match.groups())
                    current_seconds = h * 3600 + m * 60 + s
                    percent = min(100, (current_seconds / total_duration_seconds) * 100)
                    progress.update(task_id, completed=percent)
        
        # Process any remaining output
        process.communicate()
        
        # Check if process was successful
        if process.returncode != 0:
            raise Exception(f"FFmpeg conversion failed with return code {process.returncode}")
        
        # Remove the original file and update the file info
        os.remove(input_file)
        file_info['file'] = output_file
        
        # Mark task as complete for progress tracking
        if progress_tracker and task_id:
            progress_tracker.complete_task(task_id)
        
        if progress and task_id:
            basename = os.path.basename(output_file)
            progress.update(task_id, completed=100, description=f"[green]Converted: {basename}[/green]")
        
        return file_info
    except Exception as e:
        if progress and task_id:
            progress.update(task_id, description=f"[red]Conversion failed: {str(e)}[/red]")
        file_info['status'] = 'error'
        file_info['error'] = f"Conversion error: {str(e)}"
        return file_info

def main():
    """Main function to handle command-line arguments and execute the program."""
    parser = argparse.ArgumentParser(
        description='YouTube Music Downloader - Download YouTube videos/playlists as audio or video',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('url', help='YouTube video or playlist URL')
    parser.add_argument('--video', action='store_true', help='Download as video instead of audio')
    parser.add_argument('--format', choices=['mp3', 'wav', 'opus', 'm4a'], default='mp3', 
                        help='Audio format (ignored if --video is used)')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'], default='medium',
                        help='Quality setting for download')
    parser.add_argument('--parallel-download', type=int, default=3, choices=range(0, 9),
                        help='Number of parallel downloads (0 for sequential)')
    parser.add_argument('--parallel-convert', type=int, default=1, choices=range(0, 9),
                        help='Number of parallel conversions (0 for sequential)')
    parser.add_argument('--output-dir', default='downloads',
                        help='Directory to save downloaded files')
    parser.add_argument('--force', action='store_true', 
                        help='Force download even if files already exist')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Initialize objects
    file_manager = FileManager(output_dir=args.output_dir)
    progress_tracker = ProgressTracker(console=console, max_visible=5)
    downloader = YouTubeDownloader(file_manager=file_manager, progress_tracker=progress_tracker)
    converter = AudioConverter(file_manager=file_manager, progress_tracker=progress_tracker)
    
    # Validate URL
    url_type = downloader.validate_url(args.url)
    if not url_type:
        console.print("[bold red]Error: Invalid YouTube URL. Please provide a valid YouTube video or playlist URL.[/bold red]")
        return 1
    
    # Print information about the download
    console.print(f"[bold green]YouTube {'Video' if url_type == 'video' else 'Playlist'} Downloader[/bold green]")
    console.print(f"[cyan]URL: {args.url}[/cyan]")
    console.print(f"[cyan]Type: {'Video' if url_type == 'video' else 'Playlist'}[/cyan]")
    console.print(f"[cyan]Output Format: {'Video' if args.video else args.format.upper()}[/cyan]")
    console.print(f"[cyan]Quality: {args.quality.title()}[/cyan]")
    console.print(f"[cyan]Output Directory: {args.output_dir}[/cyan]")
    
    # Process the download with progress tracking
    with progress_tracker.create_progress() as progress:
        try:
            start_time = time.time()
            console.print("\n[bold cyan]Starting downloads...[/bold cyan]")
            
            # Download the videos
            results = downloader.process_url(
                args.url, 
                output_format=args.format,
                quality=args.quality,
                is_video=args.video,
                force=args.force,
                parallel=args.parallel_download
            )
            
            console.print("\n[bold cyan]Downloads completed![/bold cyan]")
            
            # Convert files if needed
            if not args.video and any(r.status == 'success' for r in results):
                console.print("\n[bold cyan]Processing audio conversions...[/bold cyan]")
                results = converter.batch_convert(
                    results,
                    args.format,
                    args.quality,
                    args.parallel_convert
                )
            
            # Print summary
            print_download_summary(results)
            
            # Clean up temporary files
            file_manager.cleanup_temp_directory()
            
            elapsed_time = time.time() - start_time
            console.print(f"\n[bold green]Total execution time: {elapsed_time:.2f} seconds[/bold green]")
            
            return 0
            
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Operation cancelled by user. Cleaning up...[/bold yellow]")
            file_manager.cleanup_temp_directory()
            return 1
        except Exception as e:
            console.print(f"\n[bold red]An error occurred: {str(e)}[/bold red]")
            file_manager.cleanup_temp_directory()
            return 1

def print_download_summary(results):
    """Print a summary of the download results."""
    console.print("\n[bold green]Download Summary:[/bold green]")
    
    success_count = sum(1 for r in results if r.status == 'success')
    error_count = sum(1 for r in results if r.status == 'error')
    skipped_count = sum(1 for r in results if r.status == 'skipped')
    
    console.print(f"[green]Successfully downloaded: {success_count}[/green]")
    console.print(f"[yellow]Skipped (already exists): {skipped_count}[/yellow]")
    console.print(f"[{'red' if error_count > 0 else 'green'}]Failed downloads: {error_count}[/{'red' if error_count > 0 else 'green'}]")
    
    if success_count > 0:
        console.print("\n[bold green]Successfully downloaded files:[/bold green]")
        for result in [r for r in results if r.status == 'success']:
            console.print(f"[cyan]- {result.title}[/cyan] -> [green]{result.file_path}[/green]")
    
    if skipped_count > 0:
        console.print("\n[bold yellow]Skipped files (already exist):[/bold yellow]")
        for result in [r for r in results if r.status == 'skipped']:
            console.print(f"[cyan]- {result.title}[/cyan] -> [yellow]{result.file_path}[/yellow]")
    
    if error_count > 0:
        console.print("\n[bold red]Failed downloads:[/bold red]")
        for result in [r for r in results if r.status == 'error']:
            console.print(f"[red]- {result.title or result.url}: {result.error}[/red]")

if __name__ == "__main__":
    # If we're being executed through another script,
    # we might need to handle a different path context
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    
    # Change to the script's directory to ensure we can find other resources
    if os.getcwd() != script_dir:
        os.chdir(script_dir)
    
    sys.exit(main())