"""File management utilities for checking and organizing downloads."""
import os

from ripper.config import DOWNLOADS_DIR


def file_exists(artist: str, song: str) -> bool:
    """Check if a file already exists in the downloads directory.
    
    Args:
        artist: Artist name
        song: Song name
        
    Returns:
        True if file exists, False otherwise
    """
    expected_filename = f"{song} - {artist}.mp3"
    expected_path = os.path.join(DOWNLOADS_DIR, expected_filename)
    return os.path.exists(expected_path)


def get_expected_filepath(artist: str, song: str) -> str:
    """Get the expected filepath for a given artist and song.
    
    Args:
        artist: Artist name
        song: Song name
        
    Returns:
        Full path to where the file would be saved
    """
    filename = f"{song} - {artist}.mp3"
    return os.path.join(DOWNLOADS_DIR, filename)
