# 🎵 YouTube Music Downloader

A powerful Python command-line tool to download YouTube videos or playlists as audio files or videos.

## ✨ Features

- 📥 Download single videos or complete playlists
- 🔄 Convert videos to audio (mp3, wav, opus, m4a)
- ⚡ Parallel downloads and conversions for better performance
- 📊 Live progress bars with download speed information
- 🔍 Skip existing files to avoid redundant downloads
- 🛑 Graceful cancellation with automatic cleanup
- 🎚️ Quality settings (low, medium, high)
- 🎬 Download videos in different resolutions

## 📋 Requirements

- 🐍 Python 3.6+
- 🎞️ FFmpeg installed on your system
- 📦 Required Python packages (see requirements.txt)

## 🚀 Installation

1. Clone this repository or download the files:
   ```
   git clone https://github.com/YoruAkio/youtube-music-downloader.git
   cd youtube-music-downloader
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg (if not already installed):
   - **Linux**: `sudo apt install ffmpeg` (Debian/Ubuntu) or use your distro's package manager
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [FFmpeg's official website](https://ffmpeg.org/download.html)

## 🎮 Usage

### Basic Usage

```
python main.py [YouTube URL]
```

Or you can use the launcher script:

```
python launcher.py [YouTube URL]
```

This will download the video or playlist as MP3 files at medium quality.

### Command-line Options

```
python main.py [YouTube URL] [OPTIONS]
```

Available options:
- `--video`: Download as video instead of extracting audio
- `--format {mp3,wav,opus,m4a}`: Audio format (default: mp3)
- `--quality {low,medium,high}`: Quality setting (default: medium)
- `--parallel-download N`: Number of parallel downloads (0-8, default: 3)
- `--parallel-convert N`: Number of parallel conversions (0-8, default: 1)
- `--output-dir DIR`: Directory to save downloaded files (default: "downloads")
- `--force`: Force download even if files already exist

### 📝 Examples

Download a YouTube video as MP3:
```
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Download a YouTube playlist as high-quality WAV files:
```
python main.py https://www.youtube.com/playlist?list=PLdSUTU0oamAgi8Uwyfz5Xq-MHlIFLJRxH --format wav --quality high
```

Download a YouTube video in video format at medium quality:
```
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --video
```

Download a playlist with 5 parallel downloads:
```
python main.py https://www.youtube.com/playlist?list=PLdSUTU0oamAgi8Uwyfz5Xq-MHlIFLJRxH --parallel-download 5
```

Force re-download of files that already exist:
```
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --force
```

## ⚠️ Cancellation

If you need to cancel a download in progress, press `Ctrl+C`. The application will clean up temporary files.

## 🎚️ Quality Settings

| Quality | Audio Bitrate | Video Resolution |
|---------|--------------|------------------|
| 🔉 Low  | 128 kbps     | 360p             |
| 🔊 Medium | 192 kbps     | 480p             |
| 🎧 High | 320 kbps     | 720p             |

## 🔧 Building From Source

The project can be built into standalone executables for Windows, macOS, and Linux using the GitHub Actions workflow. You can download the pre-built binaries from the [Releases](https://github.com/YoruAkio/youtube-music-downloader/releases) page.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

- **YoruAkio** 