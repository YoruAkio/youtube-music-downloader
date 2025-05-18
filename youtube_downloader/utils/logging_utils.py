"""
Logging utilities for YouTube Music Downloader.

This module provides utilities for setting up logging across the application.
"""

import logging
from rich.logging import RichHandler

def configure_logging(verbose=False):
    """
    Configure the application logging system.
    
    Args:
        verbose: Whether to enable verbose (debug) logging
    
    Returns:
        logging.Logger: The configured root logger
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure the root logger with rich handler
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Set our application logger levels
    app_logger = logging.getLogger("youtube_downloader")
    app_logger.setLevel(log_level)
    
    # Create specific loggers for main components
    components = ["file_utils", "downloader", "converter", "progress"]
    for component in components:
        component_logger = logging.getLogger(f"youtube_downloader.{component}")
        component_logger.setLevel(log_level)
    
    if verbose:
        app_logger.debug("Verbose logging enabled")
    
    return app_logger

def get_logger(name, verbose=False):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        verbose: Whether verbose logging is enabled
    
    Returns:
        logging.Logger: The configured logger
    """
    logger = logging.getLogger(f"youtube_downloader.{name}")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger 