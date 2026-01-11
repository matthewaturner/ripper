"""Sources package for audio download sources."""
from typing import List, Dict, Optional
from dotenv import load_dotenv

from .youtube.youtube_source import YouTubeSource
from .spotify.spotify_source import SpotifySource
from .soundcloud.soundcloud_source import SoundCloudSource

__all__ = ['YouTubeSource', 'SpotifySource', 'SoundCloudSource', 'AudioRipper']


class AudioRipper:
    """Main class for handling audio ripping from multiple sources."""
    
    def __init__(self, downloads_dir: Optional[str] = None):
        self.downloads_dir = downloads_dir
        self.source_classes = {
            'youtube': YouTubeSource,
            'soundcloud': SoundCloudSource,
            'spotify': SpotifySource
        }
        self.sources = {}  # Initialize empty, load sources on demand
        
    def get_source(self, source: str):
        """Get or initialize a source."""
        if source not in self.source_classes:
            raise ValueError(f"Unknown source: {source}")
            
        if source not in self.sources:
            # Load environment variables only when first source is initialized
            if not self.sources:
                load_dotenv()
            self.sources[source] = self.source_classes[source](downloads_dir=self.downloads_dir)
            
        return self.sources[source]

    def search_source(self, source: str, query: str, max_results: int = 5) -> List[Dict]:
        """Search a specific source for tracks."""
        try:
            return self.get_source(source).search_tracks(query, max_results)
        except Exception as e:
            print(f"Error searching {source}: {e}")
            return []

    def search_all_sources(self, query: str, max_results: int = 5, preferred_source: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Search across available sources, prioritizing preferred source.
        
        All sources are searched (except Spotify which is for playlists only).
        Results are ordered with preferred_source first if specified.
        """
        results = {}
        
        # Search all sources (except Spotify which is for playlists only)
        for source in self.source_classes:
            if source != 'spotify':  # Skip Spotify as it's for playlists only
                source_results = self.search_source(source, query, max_results)
                if source_results:
                    results[source] = source_results
        
        # If preferred source is specified and has results, ensure it's first
        if preferred_source and preferred_source in results:
            # Reorder dict to put preferred source first
            reordered = {preferred_source: results[preferred_source]}
            for source, source_results in results.items():
                if source != preferred_source:
                    reordered[source] = source_results
            results = reordered
            
        return results

    def download_track(self, source: str, url: str, artist: str, song: str, spotify_track_id: Optional[str] = None) -> Optional[str]:
        """Download a track using the specified source."""
        try:
            return self.get_source(source).download_track(url, artist, song, spotify_track_id=spotify_track_id)
        except Exception as e:
            print(f"Error downloading from {source}: {e}")
            return None
