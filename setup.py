#!/usr/bin/env python3

"""
Setup script for YouTube Music Downloader.
"""

from setuptools import setup, find_packages
from youtube_downloader import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="youtube-music-downloader",
    version=__version__,
    author="Yoruakio",
    author_email="yoruakio@proton.me",
    description="A command-line tool to download YouTube videos and playlists as audio or video",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yoruakio/youtube-music-downloader",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "yt-dlp>=2023.11.16",
        "ffmpeg-python>=0.2.0",
        "rich>=13.4.2",
        "certifi>=2023.7.22",
    ],
    entry_points={
        "console_scripts": [
            "youtube-music-downloader=youtube_downloader.cli:main",
        ],
    },
) 