# 🎵 YouTube Music Downloader

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/YoruAkio/youtube-music-downloader?style=flat-square)
![GitHub forks](https://img.shields.io/github/forks/YoruAkio/youtube-music-downloader?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/YoruAkio/youtube-music-downloader?style=flat-square)
![GitHub license](https://img.shields.io/github/license/YoruAkio/youtube-music-downloader?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/YoruAkio/youtube-music-downloader?style=flat-square)

**Fast, efficient YouTube content downloader with an intuitive command-line interface**
</div>

---

## 🌟 Why Choose This Tool?

YouTube Music Downloader stands out with:

- 🔋 **High performance** - Download entire playlists in minutes with multi-threading
- 🧠 **Smart downloading** - Automatically skips existing files unless forced to redownload
- 📊 **Live progress tracking** - Real-time visualization of download and conversion status
- 🔄 **Format flexibility** - Download as video or convert to multiple audio formats (mp3/wav/opus/m4a)
- 🎮 **User-friendly CLI** - Simple interface with rich visual feedback using progress bars
- 🧹 **Clean operation** - Automatic cleanup of temporary files, even when cancelled

## ✨ Features in Detail

### 📥 Comprehensive Content Support
- Download individual videos with perfect metadata retention
- Process entire playlists with intelligent continuation
- Support for various YouTube URL formats

### 🔊 Audio Processing
- **Multiple formats**: Convert to MP3, WAV, OPUS, or M4A
- **Quality control**: Select from low (128kbps), medium (192kbps), or high (320kbps) audio quality
- **Smart conversion**: Efficient audio extraction minimizes quality loss

### 🎬 Video Capabilities
- Download videos in various resolutions (360p, 480p, 720p)
- Maintain original video quality with accompanying audio
- Preserve all metadata in downloaded files

### ⚡ Performance Optimization
- Parallel downloads (configurable up to 8 simultaneous downloads)
- Concurrent audio conversions for faster processing
- Efficient disk usage with temporary file management

## 📋 Requirements

- **Python 3.6+** - Core runtime environment
- **FFmpeg** - Required for audio conversion and video processing
- **Python packages**:
  - yt-dlp - Core download engine
  - rich - Terminal formatting and progress bars

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YoruAkio/youtube-music-downloader.git
   cd youtube-music-downloader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (if not already present):
   - **Linux**: 
     ```bash
     # Debian/Ubuntu
     sudo apt install ffmpeg
     
     # Arch Linux
     sudo pacman -S ffmpeg
     
     # Fedora
     sudo dnf install ffmpeg
     ```
   - **macOS**: 
     ```bash
     brew install ffmpeg
     ```
   - **Windows**: 
     Download from [ffmpeg.org](https://ffmpeg.org/download.html) or install with:
     ```bash
     choco install ffmpeg  # Using Chocolatey
     # or
     winget install FFmpeg  # Using Windows Package Manager
     ```

## 🎮 Usage

### Basic Command

```bash
python main.py [YouTube URL]
```

### Full Command Syntax

```bash
python main.py [YouTube URL] [OPTIONS]
```

### Options Reference

| Option | Description | Values | Default |
|--------|-------------|--------|---------|
| `--video` | Download as video instead of audio | Flag | Audio mode |
| `--format` | Audio format to convert to | mp3, wav, opus, m4a | mp3 |
| `--quality` | Quality setting for download | low, medium, high | medium |
| `--parallel-download` | Number of simultaneous downloads | 0-8 (0 = sequential) | 3 |
| `--parallel-convert` | Number of simultaneous conversions | 0-8 (0 = sequential) | 1 |
| `--output-dir` | Directory to save downloaded files | Any valid path | "downloads" |
| `--force` | Override existing files | Flag | Skip existing files |

## 📝 Examples

### Audio Downloads

```bash
# Download a single video as MP3 (medium quality)
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Download a video in high-quality WAV format
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --format wav --quality high

# Download a playlist as opus files with 5 simultaneous downloads
python main.py https://www.youtube.com/playlist?list=PLdSUTU0oamAgi8Uwyfz5Xq-MHlIFLJRxH --format opus --parallel-download 5
```

### Video Downloads

```bash
# Download a video in medium quality (480p)
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --video

# Download a video in high quality (720p)
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --video --quality high

# Download a playlist of videos with 4 parallel downloads
python main.py https://www.youtube.com/playlist?list=PLdSUTU0oamAgi8Uwyfz5Xq-MHlIFLJRxH --video --parallel-download 4
```

### Advanced Usage

```bash
# Force re-download of files that already exist
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --force

# Download to a custom directory
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --output-dir "my_music/favorites"

# Download a playlist, convert to M4A, with maximum parallelism
python main.py https://www.youtube.com/playlist?list=PLdSUTU0oamAgi8Uwyfz5Xq-MHlIFLJRxH --format m4a --parallel-download 8 --parallel-convert 4
```

## ⚙️ Configuration

### Quality Settings in Detail

| Setting | Audio Bitrate | Video Resolution | Best For |
|---------|--------------|------------------|----------|
| 🔉 Low  | 128 kbps     | 360p             | Saving space, older devices |
| 🔊 Medium | 192 kbps     | 480p             | Balanced quality/size |
| 🎧 High | 320 kbps     | 720p             | Best quality, modern devices |

### Cancellation & Control

Press `Ctrl+C` at any time to gracefully cancel the download process. The application will:
- Complete the current file operation if possible
- Clean up any temporary files
- Preserve already downloaded files

## ⚠️ Troubleshooting

### Common Issues

- **FFmpeg not found**: Ensure FFmpeg is installed and in your system PATH
- **Download fails**: Check your internet connection and verify the YouTube URL is valid
- **Permission errors**: Make sure you have write permissions to the output directory
- **Format issues**: Some videos may not be available in certain formats or quality levels

### Error Resolution

If you encounter issues:
1. Try running with the `--force` flag to restart the download
2. Check the YouTube URL is still valid and accessible
3. Ensure all dependencies are up to date with `pip install -r requirements.txt --upgrade`
4. Verify FFmpeg is correctly installed with `ffmpeg -version`

## 📥 Downloads

Pre-built executables are available for:
- Windows (.exe)
- macOS (.app)
- Linux (binary)

Download the latest release from the [GitHub Releases page](https://github.com/YoruAkio/youtube-music-downloader/releases).

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or suggest features through [issues](https://github.com/YoruAkio/youtube-music-downloader/issues)
- Submit [pull requests](https://github.com/YoruAkio/youtube-music-downloader/pulls) with improvements
- Share the tool with others who might find it useful

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.