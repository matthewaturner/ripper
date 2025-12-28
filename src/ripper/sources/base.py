"""Base interface for audio sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class AudioSource(ABC):
    """Base class for all audio sources (YouTube, Spotify, SoundCloud)."""
    
    @abstractmethod
    def search_tracks(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for tracks matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing track information
        """
        pass
    
    @abstractmethod
    def download_track(self, url: str, artist: str, song: str, output_path: Optional[str] = None, spotify_track_id: Optional[str] = None) -> Optional[str]:
        """Download a track from the source.
        
        Args:
            url: URL of the track to download
            artist: Artist name for metadata
            song: Song title for metadata
            output_path: Optional path to save the file to
            spotify_track_id: Optional Spotify track ID to include in filename
            
        Returns:
            Path to the downloaded file if successful, None otherwise
        """
        pass
