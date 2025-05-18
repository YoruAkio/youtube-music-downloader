"""
YouTube Music Downloader Application Module.

This module contains the main application class for the YouTube Music Downloader.
"""

import sys
import time
import argparse
import logging
from rich.console import Console

from youtube_downloader import __version__
from youtube_downloader.utils.progress import ProgressTracker
from youtube_downloader.utils.file_utils import FileManager
from youtube_downloader.utils.ssl_helper import fix_ssl_certificates
from youtube_downloader.utils.logging_utils import configure_logging
from youtube_downloader.core.downloader import YouTubeDownloader
from youtube_downloader.core.converter import AudioConverter

# Fix SSL certificates for frozen applications
fix_ssl_certificates()

# Create a logger
logger = logging.getLogger("youtube_downloader")

class YouTubeMusicDownloaderApp:
    """Main application class for YouTube Music Downloader.
    
    This class follows the Single Responsibility Principle by focusing
    solely on coordinating the application's components and workflow.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.console = Console()
        self.args = None
        self.file_manager = None
        self.progress_tracker = None
        self.downloader = None
        self.converter = None
        self.logger = None  # Will be initialized when arguments are parsed
        

    
    def parse_arguments(self):
        """Parse command-line arguments.
        
        Returns:
            argparse.Namespace: The parsed command-line arguments.
        """
        parser = argparse.ArgumentParser(
            description='YouTube Music Downloader - Download YouTube videos/playlists as audio or video',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument('url', help='YouTube video or playlist URL')
        parser.add_argument('--video', action='store_true', 
                           help='Download as video instead of audio')
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
        parser.add_argument('--verbose', action='store_true',
                           help='Enable verbose logging for debugging')
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        
        self.args = parser.parse_args()
        return self.args
    
    def initialize_components(self):
        """Initialize all application components.
        
        This method follows the Dependency Inversion Principle by injecting
        dependencies rather than creating tightly coupled components.
        """
        self.logger.debug("Initializing FileManager")
        self.file_manager = FileManager(
            output_dir=self.args.output_dir,
            logger=self.logger,
            verbose=self.args.verbose
        )
        
        self.logger.debug("Initializing ProgressTracker")
        self.progress_tracker = ProgressTracker(
            console=self.console, 
            max_visible=5,
            logger=self.logger,
            verbose=self.args.verbose
        )
        
        self.logger.debug("Initializing YouTubeDownloader")
        self.downloader = YouTubeDownloader(
            file_manager=self.file_manager, 
            progress_tracker=self.progress_tracker,
            logger=self.logger,
            verbose=self.args.verbose
        )
        
        self.logger.debug("Initializing AudioConverter")
        self.converter = AudioConverter(
            file_manager=self.file_manager, 
            progress_tracker=self.progress_tracker,
            logger=self.logger,
            verbose=self.args.verbose
        )
    
    def print_info(self, url_type):
        """Print information about the download.
        
        Args:
            url_type (str): Type of URL ('video' or 'playlist').
        """
        self.console.print(f"[bold green]YouTube {'Video' if url_type == 'video' else 'Playlist'} Downloader[/bold green]")
        self.console.print(f"[cyan]URL: {self.args.url}[/cyan]")
        self.console.print(f"[cyan]Type: {'Video' if url_type == 'video' else 'Playlist'}[/cyan]")
        self.console.print(f"[cyan]Output Format: {'Video' if self.args.video else self.args.format.upper()}[/cyan]")
        self.console.print(f"[cyan]Quality: {self.args.quality.title()}[/cyan]")
        self.console.print(f"[cyan]Output Directory: {self.args.output_dir}[/cyan]")
    
    def print_download_summary(self, results):
        """Print a summary of the download results.
        
        Args:
            results (list): List of DownloadResult objects.
        """
        self.console.print("\n[bold green]Download Summary:[/bold green]")
        
        success_count = sum(1 for r in results if r.status == 'success')
        error_count = sum(1 for r in results if r.status == 'error')
        skipped_count = sum(1 for r in results if r.status == 'skipped')
        
        self.console.print(f"[green]Successfully downloaded: {success_count}[/green]")
        self.console.print(f"[yellow]Skipped (already exists): {skipped_count}[/yellow]")
        self.console.print(f"[{'red' if error_count > 0 else 'green'}]Failed downloads: {error_count}[/{'red' if error_count > 0 else 'green'}]")
        
        if success_count > 0:
            self.console.print("\n[bold green]Successfully downloaded files:[/bold green]")
            for result in [r for r in results if r.status == 'success']:
                self.console.print(f"[cyan]- {result.title}[/cyan] -> [green]{result.file_path}[/green]")
        
        if skipped_count > 0:
            self.console.print("\n[bold yellow]Skipped files (already exist):[/bold yellow]")
            for result in [r for r in results if r.status == 'skipped']:
                self.console.print(f"[cyan]- {result.title}[/cyan] -> [yellow]{result.file_path}[/yellow]")
        
        if error_count > 0:
            self.console.print("\n[bold red]Failed downloads:[/bold red]")
            for result in [r for r in results if r.status == 'error']:
                self.console.print(f"[red]- {result.title or result.url}: {result.error}[/red]")

    def download_and_convert(self):
        """Handle the download and conversion process.
        
        This method follows the Single Responsibility Principle by
        handling only the core download and conversion workflow.
        
        Returns:
            int: Exit code (0 for success, 1 for failure).
        """
        with self.progress_tracker.create_progress() as progress:
            try:
                start_time = time.time()
                self.logger.info("Starting download process")
                self.console.print("\n[bold cyan]Starting downloads...[/bold cyan]")
                
                # Download the videos
                self.logger.debug(f"Download settings: format={self.args.format}, quality={self.args.quality}, is_video={self.args.video}, parallel={self.args.parallel_download}")
                results = self.downloader.process_url(
                    self.args.url, 
                    output_format=self.args.format,
                    quality=self.args.quality,
                    is_video=self.args.video,
                    force=self.args.force,
                    parallel=self.args.parallel_download
                )
                
                self.logger.info("Downloads completed")
                self.console.print("\n[bold cyan]Downloads completed![/bold cyan]")
                
                # Convert files if needed
                if not self.args.video and any(r.status == 'success' for r in results):
                    self.logger.info("Starting audio conversion process")
                    self.console.print("\n[bold cyan]Processing audio conversions...[/bold cyan]")
                    results = self.converter.batch_convert(
                        results,
                        self.args.format,
                        self.args.quality,
                        self.args.parallel_convert
                    )
                
                # Print summary
                self.logger.info("Preparing download summary")
                self.print_download_summary(results)
                
                # Clean up temporary files
                self.logger.debug("Cleaning up temporary files")
                self.file_manager.cleanup_temp_directory()
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
                self.console.print(f"\n[bold green]Total execution time: {elapsed_time:.2f} seconds[/bold green]")
                
                return 0
                
            except KeyboardInterrupt:
                self.logger.warning("Operation cancelled by user")
                self.console.print("\n[bold yellow]Operation cancelled by user. Cleaning up...[/bold yellow]")
                self.file_manager.cleanup_temp_directory()
                return 1
            except Exception as e:
                self.logger.error(f"An error occurred: {str(e)}", exc_info=True)
                self.console.print(f"\n[bold red]An error occurred: {str(e)}[/bold red]")
                self.file_manager.cleanup_temp_directory()
                return 1
    
    def run(self):
        """Execute the main application workflow.
        
        This method orchestrates the entire application flow following
        the Single Responsibility Principle by delegating tasks to
        specialized methods.
        
        Returns:
            int: Exit code (0 for success, 1 for failure).
        """
        # Parse command-line arguments
        self.parse_arguments()
        
        # Set up logging based on verbose flag
        self.logger = configure_logging(verbose=self.args.verbose)
        
        self.logger.debug("Starting YouTube Music Downloader")
        
        # Initialize components
        self.logger.debug("Initializing application components")
        self.initialize_components()
        
        # Validate URL
        self.logger.debug(f"Validating URL: {self.args.url}")
        url_type = self.downloader.validate_url(self.args.url)
        if not url_type:
            self.logger.error(f"Invalid YouTube URL: {self.args.url}")
            self.console.print("[bold red]Error: Invalid YouTube URL. Please provide a valid YouTube video or playlist URL.[/bold red]")
            return 1
        
        # Print information about the download
        self.logger.info(f"Processing {url_type} URL: {self.args.url}")
        self.print_info(url_type)
        
        # Process the download and conversion
        self.logger.debug("Starting download and conversion process")
        return self.download_and_convert() 