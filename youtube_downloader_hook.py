"""
PyInstaller hook file for YouTube Music Downloader.

This file helps PyInstaller to include all necessary modules.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all submodules and data files from the youtube_downloader package
datas, binaries, hiddenimports = collect_all('youtube_downloader')

# Add additional submodules that might be imported dynamically
hiddenimports.extend([
    'youtube_downloader.app',
    'youtube_downloader.cli',
    'youtube_downloader.core.downloader',
    'youtube_downloader.core.converter',
    'youtube_downloader.utils.progress',
    'youtube_downloader.utils.file_utils',
    'youtube_downloader.utils.ssl_helper',
])

# Include yt-dlp dependencies
hiddenimports.extend(collect_submodules('yt_dlp'))

# Include rich dependencies
hiddenimports.extend(collect_submodules('rich'))

# Include certifi for SSL certificate handling
hiddenimports.extend(['certifi', 'ssl']) 