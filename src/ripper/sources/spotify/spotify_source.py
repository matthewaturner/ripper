"""Spotify integration for fetching track information."""
import os
from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from ..base import AudioSource
from ripper.utils.formatting import format_track_info

class SpotifySource:
    """Spotify source for fetching track information and playlists."""
    
    def __init__(self, downloads_dir: Optional[str] = None):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Spotify credentials not found. Please set them in .env file")
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope='playlist-read-private playlist-modify-public playlist-modify-private'
        ))

    def get_playlist_tracks(self, playlist_uri: str) -> List[Dict]:
        """Export all tracks from a Spotify playlist.
        
        Args:
            playlist_uri: Spotify playlist URI (spotify:playlist:ID) or ID
            
        Returns:
            List of track information dictionaries
        """
        try:
            # Handle different formats:
            # 1. URI format: spotify:playlist:37i9dQZF1DWWQRwui0ExPn
            # 2. URL format: https://open.spotify.com/playlist/37i9dQZF1DWWQRwui0ExPn?si=...
            # 3. Direct ID: 37i9dQZF1DWWQRwui0ExPn
            
            if playlist_uri.startswith('http'):
                # Extract ID from URL
                playlist_id = playlist_uri.split('playlist/')[1].split('?')[0]
            elif ':' in playlist_uri:
                # Extract ID from URI
                playlist_id = playlist_uri.split(':')[-1]
            else:
                # Assume it's already an ID
                playlist_id = playlist_uri

            tracks = []
            results = self.sp.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    track = item['track']
                    if track:  # Some tracks might be None if they've been removed
                        track_info = {
                            'artist': track['artists'][0]['name'],  # Using first artist
                            'song': track['name'],
                            'album': track['album']['name'],
                            'year': track['album']['release_date'][:4],
                            'duration': track['duration_ms'] // 1000,  # Convert to seconds
                            'spotify_track_id': track['id']
                        }
                        tracks.append(format_track_info(track_info))
                
                results = self.sp.next(results) if results['next'] else None
            
            return tracks
            
        except Exception as e:
            print(f"Error fetching playlist: {e}")
            return []

    def search_track(self, artist: str, song: str) -> Optional[Dict]:
        """Search for a specific track on Spotify.
        
        Args:
            artist: Artist name
            song: Song title
            
        Returns:
            Track information dictionary if found, None otherwise
        """
        try:
            query = f"artist:{artist} track:{song}"
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results and results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_info = {
                    'artist': track['artists'][0]['name'],
                    'song': track['name'],
                    'album': track['album']['name'],
                    'year': track['album']['release_date'][:4],
                    'duration': track['duration_ms'] // 1000,
                    'spotify_track_id': track['id']
                }
                return format_track_info(track_info)
            return None
            
        except Exception as e:
            print(f"Error searching track: {e}")
            return None

    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """Get track information by Spotify track ID.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Track information dictionary if found, None otherwise
        """
        try:
            track = self.sp.track(track_id)
            if track:
                track_info = {
                    'artist': track['artists'][0]['name'],
                    'song': track['name'],
                    'album': track['album']['name'],
                    'year': track['album']['release_date'][:4],
                    'duration': track['duration_ms'] // 1000,
                    'spotify_track_id': track['id']
                }
                return format_track_info(track_info)
            return None
        except Exception as e:
            print(f"Error fetching track by ID: {e}")
            return None

    def get_playlist_info(self, playlist_uri: str) -> Optional[Dict]:
        """Get basic playlist information.
        
        Args:
            playlist_uri: Spotify playlist URI (spotify:playlist:ID) or ID
            
        Returns:
            Dictionary with playlist name and ID
        """
        try:
            playlist_id = self._extract_playlist_id(playlist_uri)
            playlist = self.sp.playlist(playlist_id, fields='name,id,owner')
            return {
                'name': playlist['name'],
                'id': playlist['id'],
                'owner': playlist['owner']['display_name']
            }
        except Exception as e:
            print(f"Error fetching playlist info: {e}")
            return None

    def add_tracks_to_playlist(self, playlist_uri: str, track_ids: List[str]) -> bool:
        """Add tracks to a Spotify playlist.
        
        Args:
            playlist_uri: Spotify playlist URI (spotify:playlist:ID) or ID
            track_ids: List of Spotify track IDs to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_id = self._extract_playlist_id(playlist_uri)
            # Spotify API allows max 100 tracks per request
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i + 100]
                self.sp.playlist_add_items(playlist_id, batch)
            return True
        except Exception as e:
            print(f"Error adding tracks to playlist: {e}")
            return False

    def remove_tracks_from_playlist(self, playlist_uri: str, track_ids: List[str]) -> bool:
        """Remove tracks from a Spotify playlist.
        
        Args:
            playlist_uri: Spotify playlist URI (spotify:playlist:ID) or ID
            track_ids: List of Spotify track IDs to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_id = self._extract_playlist_id(playlist_uri)
            # Spotify API allows max 100 tracks per request
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i + 100]
                self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
            return True
        except Exception as e:
            print(f"Error removing tracks from playlist: {e}")
            return False

    def _extract_playlist_id(self, playlist_uri: str) -> str:
        """Extract playlist ID from URI, URL, or direct ID.
        
        Args:
            playlist_uri: Spotify playlist URI, URL, or ID
            
        Returns:
            Playlist ID
        """
        if playlist_uri.startswith('http'):
            # Extract ID from URL
            return playlist_uri.split('playlist/')[1].split('?')[0]
        elif ':' in playlist_uri:
            # Extract ID from URI
            return playlist_uri.split(':')[-1]
        else:
            # Assume it's already an ID
            return playlist_uri
