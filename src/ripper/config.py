"""Configuration settings for the audio ripper."""
from pathlib import Path

# Directory where downloaded files are saved
DOWNLOADS_DIR = str(Path.home() / "Downloads")

# Track matching threshold (0.0 to 1.0)
# Higher values require closer matches
MATCHING_THRESHOLD = 0.7

# Audio quality settings
# Target bitrate for MP3 encoding (when re-encoding is necessary)
FFMPEG_AUDIO_CODEC = "libmp3lame"
FFMPEG_AUDIO_BITRATE = "320k"
FFMPEG_TIMEOUT = 300  # 5 minutes

# Smart re-encoding: Only re-encode if file is not rekordbox-compatible
# Set to False to force re-encoding of all downloads (legacy behavior)
SMART_REENCODE = True

# Minimum acceptable bitrate for downloaded files (in kbps)
# Files below this will trigger re-encoding to ensure quality
MIN_ACCEPTABLE_BITRATE = 192

# Default preferred source for playlist downloads
DEFAULT_PLAYLIST_SOURCE = "soundcloud"
