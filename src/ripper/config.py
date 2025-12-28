"""Configuration settings for the audio ripper."""
from pathlib import Path

# Directory where downloaded files are saved
DOWNLOADS_DIR = str(Path.home() / "Downloads")

# Track matching threshold (0.0 to 1.0)
# Higher values require closer matches
MATCHING_THRESHOLD = 0.7

# FFmpeg encoding parameters
FFMPEG_AUDIO_CODEC = "libmp3lame"
FFMPEG_AUDIO_BITRATE = "320k"
FFMPEG_TIMEOUT = 300  # 5 minutes

# Default preferred source for playlist downloads
DEFAULT_PLAYLIST_SOURCE = "soundcloud"
