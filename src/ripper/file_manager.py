"""File management utilities for checking and organizing downloads."""
import os
from typing import Optional

from ripper.config import DOWNLOADS_DIR


def file_exists(artist: str, song: str, downloads_dir: Optional[str] = None) -> bool:
    """Check if a file already exists in the downloads directory.
    
    Args:
        artist: Artist name
        song: Song name
        downloads_dir: Optional custom downloads directory
        
    Returns:
        True if file exists, False otherwise
    """
    dir_path = downloads_dir if downloads_dir else DOWNLOADS_DIR
    expected_filename = f"{song} - {artist}.mp3"
    expected_path = os.path.join(dir_path, expected_filename)
    return os.path.exists(expected_path)


def get_expected_filepath(artist: str, song: str, downloads_dir: Optional[str] = None) -> str:
    """Get the expected filepath for a given artist and song.
    
    Args:
        artist: Artist name
        song: Song name
        downloads_dir: Optional custom downloads directory
        
    Returns:
        Full path to where the file would be saved
    """
    dir_path = downloads_dir if downloads_dir else DOWNLOADS_DIR
    filename = f"{song} - {artist}.mp3"
    return os.path.join(dir_path, filename)
