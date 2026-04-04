"""File management utilities for checking and organizing downloads."""
import os
import re
from typing import Optional

from ripper.config import DOWNLOADS_DIR


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by replacing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename safe for all filesystems
    """
    # Replace forward slashes with a safe alternative
    filename = filename.replace('/', '⧸')  # Unicode division slash
    
    # Replace other problematic characters
    # Windows: < > : " \ | ? *
    # Unix/Mac: mainly just /
    replacements = {
        '<': '‹',
        '>': '›',
        ':': '∶',
        '"': "'",
        '\\': '⧹',
        '|': '∣',
        '?': '？',
        '*': '∗'
    }
    
    for char, replacement in replacements.items():
        filename = filename.replace(char, replacement)
    
    # Remove any control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    
    return filename.strip()


def file_exists(artist: str, song: str, downloads_dir: Optional[str] = None, spotify_track_id: Optional[str] = None) -> bool:
    """Check if a file already exists in the downloads directory.
    
    Args:
        artist: Artist name
        song: Song name
        downloads_dir: Optional custom downloads directory
        spotify_track_id: Optional Spotify track ID to include in filename
        
    Returns:
        True if file exists, False otherwise
    """
    dir_path = downloads_dir if downloads_dir else DOWNLOADS_DIR
    if spotify_track_id:
        expected_filename = f"{sanitize_filename(song)} - {sanitize_filename(artist)} {{{spotify_track_id}}}.mp3"
    else:
        expected_filename = f"{sanitize_filename(song)} - {sanitize_filename(artist)}.mp3"
    expected_path = os.path.join(dir_path, expected_filename)
    return os.path.exists(expected_path)


def get_expected_filepath(artist: str, song: str, downloads_dir: Optional[str] = None, spotify_track_id: Optional[str] = None) -> str:
    """Get the expected filepath for a given artist and song.
    
    Args:
        artist: Artist name
        song: Song name
        downloads_dir: Optional custom downloads directory
        spotify_track_id: Optional Spotify track ID to include in filename
        
    Returns:
        Full path to where the file would be saved
    """
    dir_path = downloads_dir if downloads_dir else DOWNLOADS_DIR
    if spotify_track_id:
        filename = f"{sanitize_filename(song)} - {sanitize_filename(artist)} {{{spotify_track_id}}}.mp3"
    else:
        filename = f"{sanitize_filename(song)} - {sanitize_filename(artist)}.mp3"
    return os.path.join(dir_path, filename)
