# Audio Ripper

Download audio from YouTube, SoundCloud, or Spotify playlists.

## Prerequisites

- Python 3.6+
- FFmpeg
- JavaScript runtime (required for yt-dlp) - Deno recommended

## Installation

1. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Install FFmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. Install a JavaScript runtime (Deno recommended):
   - **macOS/Linux**: 
     ```bash
     curl -fsSL https://deno.land/install.sh | sh
     ```
   - **Windows**: 
     ```powershell
     irm https://deno.land/install.ps1 | iex
     ```

## Credentials

Create a `.env` file with the following:

**YouTube** (optional, for single song searches):
1. Get an API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Add to `.env`: `YOUTUBE_API_KEY=your_key_here`

**Spotify** (required for playlist downloads):
1. Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Add redirect URI: `http://localhost:8888/callback`
3. Add to `.env`:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

**SoundCloud** (optional, for single song searches):
1. Go to [soundcloud.com](https://soundcloud.com) and open Developer Tools (F12)
2. Play any track and check Network tab for API requests to `api-v2.soundcloud.com`
3. Find the `client_id` parameter and add to `.env`: `SOUNDCLOUD_CLIENT_ID=your_client_id`

## Usage

**Download a single song:**
```bash
# Interactive mode
python ripper.py

# With arguments
python ripper.py song -a "Artist Name" -s "Song Name"

# Specify preferred source
python ripper.py song -a "Artist Name" -s "Song Name" --source soundcloud
```

**Download a Spotify playlist:**
```bash
# Using playlist URI
python ripper.py playlist --uri spotify:playlist:37i9dQZF1DWWQRwui0ExPn

# Using playlist URL
python ripper.py playlist --uri https://open.spotify.com/playlist/37i9dQZF1DWWQRwui0ExPn

# Using just the ID
python ripper.py playlist --uri 37i9dQZF1DWWQRwui0ExPn

# Specify preferred source (default: soundcloud)
python ripper.py playlist --uri 37i9dQZF1DWWQRwui0ExPn --source youtube
```

Files are saved to your Downloads folder as `song - artist.m4a` or `song - artist.mp3`.
