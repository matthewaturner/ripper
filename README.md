# YouTube Audio Ripper

A simple cross-platform Python application that allows you to search YouTube, view video details, and download audio as MP3.

## Features

- Search YouTube videos with detailed metadata (title, channel, duration, views)
- Display top 5 search results
- Download audio in MP3 format
- Save files directly to Downloads folder

## Prerequisites

- Python 3.6 or higher
- FFmpeg (required for audio conversion)

## Installation

1. Clone this repository
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg` (Ubuntu/Debian) or `sudo dnf install ffmpeg` (Fedora)

4. Get a YouTube API key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Create credentials (API key)
   - Copy your API key

5. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Replace `your_api_key_here` with your actual YouTube API key

## Usage

Run the script:
```bash
python youtube_ripper.py
```

Follow the prompts to:
1. Enter a search term
2. Select from the search results (1-5)
3. Wait for the download to complete

The MP3 file will be saved to your Downloads folder.

## Future Improvements

- AI-powered metadata generation for artist, title, album, key, etc.
- Batch downloading
- Custom output directory selection
- Audio quality options

## Legal Notice

This tool is for personal use only. Please respect copyright laws and YouTube's terms of service.
