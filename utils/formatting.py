"""Utility functions for formatting durations and view counts."""
import re
from datetime import timedelta
from typing import Dict

def format_duration(duration) -> str:
    """Convert duration to readable format.
    
    Args:
        duration: Either ISO 8601 string (e.g., 'PT3M45S') or integer seconds
        
    Returns:
        Formatted duration string (e.g., '3:45' or '1:23:45')
    """
    # Handle integer duration (seconds)
    if isinstance(duration, int):
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    # Handle ISO 8601 string format (YouTube)
    if isinstance(duration, str):
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        if not match:
            return "Unknown"

        hours, minutes, seconds = match.groups()
        time_dict = {
            'hours': int(hours) if hours else 0,
            'minutes': int(minutes) if minutes else 0,
            'seconds': int(seconds) if seconds else 0
        }
        
        time_obj = timedelta(**time_dict)
        if time_dict['hours'] > 0:
            return str(time_obj)
        return str(time_obj)[2:]  # Remove leading "0:"
    
    return "Unknown"

def format_views(views: str) -> str:
    """Format view count to be more readable."""
    views_int = int(views)
    if views_int >= 1_000_000:
        return f"{views_int/1_000_000:.1f}M views"
    elif views_int >= 1_000:
        return f"{views_int/1_000:.1f}K views"
    return f"{views_int} views"

def format_track_info(track: Dict) -> Dict:
    """Format track information into a standardized format."""
    return {
        'artist': track.get('artist', ''),
        'song': track.get('song', ''),
        'album': track.get('album', ''),
        'year': track.get('year', ''),
        'duration': track.get('duration', 0)  # Duration in seconds
    }
