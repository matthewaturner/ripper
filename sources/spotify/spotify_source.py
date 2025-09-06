"""Spotify integration for fetching track information."""
import os
from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from ..base import AudioSource
from utils.formatting import format_track_info

class SpotifySource:
    """Spotify source for fetching track information and playlists."""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Spotify credentials not found. Please set them in .env file")
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope='playlist-read-private'
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
                            'duration': track['duration_ms'] // 1000  # Convert to seconds
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
                    'duration': track['duration_ms'] // 1000
                }
                return format_track_info(track_info)
            return None
            
        except Exception as e:
            print(f"Error searching track: {e}")
            return None
