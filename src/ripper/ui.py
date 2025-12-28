"""UI display and user interaction utilities."""
from typing import Dict, List, Optional, Tuple

from ripper.utils.formatting import format_duration, format_views


def display_search_results(results: Dict[str, List[Dict]]) -> Dict[int, Tuple[str, Dict]]:
    """Display search results from multiple sources and return result mapping.
    
    Args:
        results: Dictionary mapping source names to lists of search results
        
    Returns:
        Dictionary mapping result numbers to (source, result) tuples
    """
    print("\nSearch Results:")
    total_results = 0
    result_map = {}  # Map result numbers to (source, result) pairs
    
    for source, source_results in results.items():
        if source_results:
            print(f"\n{source.upper()} RESULTS:")
            for result in source_results:
                total_results += 1
                if source == 'youtube':
                    duration = format_duration(result['duration'])
                    views = format_views(result['views'])
                    print(f"\n{total_results}. [{source.upper()}] {result['title']}")
                    print(f"   Channel: {result['channel']}")
                    print(f"   Duration: {duration} | {views}")
                elif source == 'soundcloud':
                    duration = format_duration(result['duration'])
                    print(f"\n{total_results}. [{source.upper()}] {result['title']}")
                    print(f"   Artist: {result['artist']}")
                    print(f"   Duration: {duration} | Likes: {result['likes']}")
                    if result.get('genre'):
                        print(f"   Genre: {result['genre']}")
                result_map[total_results] = (source, result)
    
    return result_map


def display_spotify_track_info(spotify_data: Dict) -> None:
    """Display Spotify track metadata.
    
    Args:
        spotify_data: Dictionary containing Spotify track metadata
    """
    spotify_duration = format_duration(spotify_data['duration'])
    print(f"\nSpotify Track Info:")
    print(f"   {spotify_data['artist']} - {spotify_data['song']}")
    print(f"   Duration: {spotify_duration}")


def get_user_choice(total_results: int) -> Optional[int]:
    """Get user's choice from numbered results.
    
    Args:
        total_results: Total number of results to choose from
        
    Returns:
        Selected result number (1-indexed), or None if user chooses to skip
    """
    while True:
        try:
            choice = int(input(f"\nEnter number to download (1-{total_results}, or -1 to skip): "))
            if choice == -1:
                return None
            if 1 <= choice <= total_results:
                return choice
            print(f"Please enter a number between 1 and {total_results}, or -1 to skip")
        except ValueError:
            print("Please enter a valid number")
