"""Utilities for matching tracks between sources."""
from typing import Dict, List, Optional
from thefuzz import fuzz
import re
import isodate

def parse_duration(duration: str) -> int:
    """Convert various duration formats to seconds."""
    if isinstance(duration, int):
        return duration
    
    try:
        # Try parsing as ISO 8601 duration (YouTube format)
        if duration.startswith('PT'):
            return int(isodate.parse_duration(duration).total_seconds())
        
        # If it's already in seconds as string
        return int(duration)
        
    except Exception:
        # Return 0 if we can't parse it
        return 0


def clean_title(title: str) -> str:
    """Clean up a title for comparison."""
    # Remove common additions like "(Official Video)", "[HD]", etc.
    patterns = [
        r'\([^)]*\)',  # Anything in ()
        r'\[[^\]]*\]',  # Anything in []
        r'official\s*(video|audio|music|hd|lyric|lyrics)',
        r'lyrics\s*video',
        r'audio\s*only',
        r'full\s*album',
        r'official\s*release',
        r'explicit',
        r'original\s*mix',
        r'hq',
        r'hd',
    ]
    
    title = title.lower()
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    return " ".join(title.split())  # Normalize whitespace

def score_match(spotify_data: Dict, result: Dict, source: str) -> float:
    """Score how well a search result matches Spotify track data.
    
    Args:
        spotify_data: Track data from Spotify
        result: Search result from a source
        source: Source name ('youtube' or 'soundcloud')
        
    Returns:
        Score between 0 and 1, higher is better
    """
    score = 0.0
    max_score = 4.0  # Total of all scoring components
    
    # 1. Duration match (max 1 point)
    # Allow 3 seconds difference for perfect match, scale down to 10 seconds
    spotify_duration = parse_duration(spotify_data['duration'])
    result_duration = parse_duration(result['duration'])
    duration_diff = abs(spotify_duration - result_duration)
    if duration_diff <= 3:
        score += 1.0
    elif duration_diff <= 10:
        score += 1.0 - ((duration_diff - 3) / 7)
    
    # 2. Title match (max 1 point)
    # Clean up titles for better matching
    spotify_title = clean_title(spotify_data['song'])
    result_title = clean_title(result['title'])
    
    title_ratio = fuzz.ratio(spotify_title, result_title) / 100
    score += title_ratio
    
    # 3. Artist match (max 1 point)
    spotify_artist = spotify_data['artist'].lower()
    
    if source == 'youtube':
        # For YouTube, check both title and channel
        channel = result['channel'].lower()
        # Check if artist appears in channel name
        channel_ratio = fuzz.partial_ratio(spotify_artist, channel) / 100
        # Also check if artist appears in title
        title_artist_ratio = fuzz.partial_ratio(spotify_artist, result_title) / 100
        # Use the better of the two scores
        score += max(channel_ratio, title_artist_ratio)
    else:  # SoundCloud
        result_artist = result['artist'].lower()
        artist_ratio = fuzz.ratio(spotify_artist, result_artist) / 100
        score += artist_ratio
    
    # 4. Additional source-specific scoring (max 1 point)
    if source == 'youtube':
        # Prefer videos with more views (logarithmic scale)
        try:
            views = int(result['views'])
            view_score = min(1.0, views / 1000000)  # Max at 1M views
            score += view_score
        except (ValueError, KeyError):
            pass
    elif source == 'soundcloud':
        # Prefer tracks with more likes
        try:
            likes = int(result['likes'])
            like_score = min(1.0, likes / 10000)  # Max at 10K likes
            score += like_score
        except (ValueError, KeyError):
            pass
            
        # Bonus for genre match if available
        if result.get('genre') and spotify_data.get('genre'):
            if result['genre'].lower() == spotify_data['genre'].lower():
                score += 0.2  # Small bonus

    # Normalize score to 0-1 range
    return score / max_score

def find_best_match(spotify_data: Dict, results: List[Dict], source: str, threshold: float = 0.7) -> Optional[Dict]:
    """Find the best matching track from search results.
    
    Args:
        spotify_data: Track data from Spotify
        results: List of search results
        source: Source name ('youtube' or 'soundcloud')
        threshold: Minimum score to consider a match (0-1)
        
    Returns:
        Best matching result or None if no good matches
    """
    if not results:
        return None
        
    # Score all results
    scored_results = [
        (result, score_match(spotify_data, result, source))
        for result in results
    ]
    
    # Sort by score
    scored_results.sort(key=lambda x: x[1], reverse=True)
    best_result, best_score = scored_results[0]
    
    # Return best match if it meets threshold
    if best_score >= threshold:
        return best_result
    return None
