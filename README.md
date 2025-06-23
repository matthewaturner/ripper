# Audio Ripper

A cross-platform Python application that downloads audio from multiple sources (YouTube, SoundCloud) with Spotify playlist support.

## Features

- Multi-source audio downloading:
  - YouTube with detailed metadata (title, channel, duration, views)
  - SoundCloud with less rate limiting
  - Ability to specify preferred source
  - Automatic fallback if preferred source fails
- Display top 5 search results from each source
- Download audio in high-quality MP3/M4A format
- Save files directly to Downloads folder
- Export Spotify playlists to CSV
- Batch download from CSV files
- Proper audio metadata tagging

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

4. Get Required Credentials:
   - YouTube:
     - For search functionality:
       1. Go to [Google Cloud Console](https://console.cloud.google.com/)
       2. Create a new project or select an existing one
       3. Enable the YouTube Data API v3
       4. Create credentials (API key)
       5. Copy your API key
   - Spotify:
     - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
     - Create a new application
     - Get your Client ID and Client Secret
     - Add http://localhost:8888/callback to Redirect URIs
   - SoundCloud:
     - To get your SoundCloud client ID:
       1. Go to [SoundCloud](https://soundcloud.com) in your browser
       2. Open Developer Tools (F12)
       3. Go to the Network tab
       4. Play any track on SoundCloud
       5. Look for requests to the API (api-v2.soundcloud.com)
       6. Find the client_id parameter in the request URL
       7. Copy this value for your SOUNDCLOUD_CLIENT_ID

5. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Set `YOUTUBE_API_KEY` to your YouTube API key
   - Set `FFMPEG_PATH` to your FFmpeg installation directory
   - Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` to your Spotify credentials
   - Set `SPOTIFY_REDIRECT_URI` to http://localhost:8888/callback
   - Set `SOUNDCLOUD_CLIENT_ID` to your SoundCloud client ID

## Usage

The script provides several commands:

1. Download a single song:
```bash
# Interactive mode (searches all sources)
python ripper.py

# Command-line mode with specific source
python ripper.py song -a "Artist Name" -s "Song Name" --source soundcloud
```

2. Export a Spotify playlist to CSV:
```bash
# Three ways to specify the playlist:
# 1. Spotify URI (right-click playlist -> Share -> Copy Spotify URI)
python ripper.py playlist export --uri "spotify:playlist:37i9dQZF1DWWQRwui0ExPn" --output songs.csv

# 2. Spotify URL (copy from browser)
python ripper.py playlist export --uri "https://open.spotify.com/playlist/37i9dQZF1DWWQRwui0ExPn?si=..." --output songs.csv

# 3. Just the playlist ID
python ripper.py playlist export --uri "37i9dQZF1DWWQRwui0ExPn" --output songs.csv
```

3. Download songs from CSV:
```bash
# Use SoundCloud as preferred source (default)
python ripper.py playlist rip --input songs.csv

# Use YouTube as preferred source
python ripper.py playlist rip --input songs.csv --source youtube
```

For single songs, the script will:
1. Search across enabled sources (YouTube, SoundCloud)
2. Show search results with metadata from each source
3. Let you choose which version to download
4. Download and convert to audio file
5. Set proper metadata (artist and title)
6. Save as "song - artist.m4a" or "song - artist.mp3" (preferring m4a when available)

For playlists:
1. Export command saves playlist tracks to CSV with:
   - Artist name
   - Song title
   - Album name
   - Release year
   - Duration

2. Rip command processes the CSV and:
   - Automatically searches for each song on preferred source
   - Falls back to other sources if preferred source fails
   - Downloads the best match
   - Sets proper metadata
   - Names files consistently

All audio files are saved to your Downloads folder.

## Source Priority

By default, the script now prefers SoundCloud over YouTube when ripping from CSV, as it's less prone to rate limiting. You can override this with the --source flag.

When downloading individual songs, results from all available sources are shown, and you can choose which version to download.

## Future Improvements

- AI-powered metadata generation for artist, title, album, key, etc.
- Additional audio sources
- Custom output directory selection
- Audio quality options
- Smart matching algorithms for better search results
- Playlist creation from text files
- More granular source preferences

## Legal Notice

This tool is for personal use only. Please respect copyright laws and the terms of service of all platforms.
