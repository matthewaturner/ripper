"""Utility functions for formatting durations and view counts."""
import re
from datetime import timedelta
from typing import Dict

def format_duration(duration: str) -> str:
    """Convert YouTube duration format (ISO 8601) to readable format."""
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
