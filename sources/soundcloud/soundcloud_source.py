"""SoundCloud audio source implementation."""
import os
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
import sclib
import requests
from urllib.parse import quote
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, TIT2, TPE1

from ..base import AudioSource
from utils.formatting import format_track_info

class SoundCloudSource(AudioSource):
    """SoundCloud implementation for searching and downloading tracks."""
    
    def __init__(self):
        self.downloads_dir = str(Path.home() / "Downloads")
        self._client_id = None
        self._api = None

    def _get_client_id(self) -> Optional[str]:
        """Get a valid client ID from the SoundCloud web interface."""
        if self._client_id:
            return self._client_id

        try:
            # Get the main page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            r = requests.get('https://soundcloud.com', headers=headers)
            if not r.ok:
                raise Exception("Failed to fetch SoundCloud homepage")

            # Find the scripts containing client_id
            script_urls = re.findall(r'<script crossorigin src="([^"]+)"></script>', r.text)
            
            # Try each script until we find a client_id
            for script_url in script_urls:
                if not script_url.startswith('http'):
                    script_url = 'https://soundcloud.com' + script_url
                
                r = requests.get(script_url, headers=headers)
                if not r.ok:
                    continue

                # Look for client_id
                client_id_match = re.search(r'client_id:"([^"]+)"', r.text)
                if client_id_match:
                    self._client_id = client_id_match.group(1)
                    return self._client_id

            raise Exception("Could not find client_id in scripts")

        except Exception as e:
            print(f"Failed to get client ID: {e}")
            return None

    def _get_track_info_from_url(self, url: str) -> Optional[Dict]:
        """Get track information from a SoundCloud URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            client_id = self._get_client_id()
            if not client_id:
                raise Exception("Could not obtain valid client ID")

            # First get the track ID from the URL
            resolve_url = f"https://api-v2.soundcloud.com/resolve?url={url}&client_id={client_id}"
            r = requests.get(resolve_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to resolve URL: {r.status_code}")
            
            track_data = r.json()
            if not track_data or 'id' not in track_data:
                raise Exception("Could not get track ID")
            
            # Then get the full track info
            track_url = f"https://api-v2.soundcloud.com/tracks/{track_data['id']}?client_id={client_id}"
            r = requests.get(track_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to get track info: {r.status_code}")
            
            return r.json()
            
        except Exception as e:
            print(f"Error getting track info: {e}")
            return None

    def search_tracks(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search SoundCloud for tracks matching query using public API."""
        try:
            client_id = self._get_client_id()
            if not client_id:
                raise Exception("Could not obtain valid client ID for search")
            
            # Search using public API with encoded query
            encoded_query = quote(query)
            url = f"https://api-v2.soundcloud.com/search/tracks?q={encoded_query}&client_id={client_id}&limit={max_results}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            r = requests.get(url, headers=headers)
            if not r.ok:
                raise Exception(f"API request failed: {r.status_code}")
            
            data = r.json()
            output = []
            
            for track in data.get('collection', []):
                output.append({
                    'id': track['id'],
                    'title': track['title'],
                    'artist': track.get('user', {}).get('username', 'Unknown Artist'),
                    'duration': track['duration'] // 1000,  # Convert ms to seconds
                    'url': track['permalink_url'],
                    'likes': track.get('likes_count', 0),
                    'genre': track.get('genre', '')
                })
            
            return output
        except Exception as e:
            print(f"Error searching tracks: {e}")
            return []

    def download_track(self, url: str, artist: str, song: str, output_path: Optional[str] = None) -> Optional[str]:
        """Download a track from SoundCloud."""
        if output_path is None:
            output_path = self.downloads_dir

        try:
            # Get track info
            track_info = self._get_track_info_from_url(url)
            if not track_info:
                raise Exception("Could not get track info")

            # Create output filename
            output_filename = f"{song} - {artist}"
            output_filepath = os.path.join(output_path, output_filename)
            
            # Download track
            print(f"\nDownloading: {track_info['title']}")
            
            # Get the stream URL
            client_id = self._get_client_id()
            if not client_id:
                raise Exception("Could not obtain valid client ID")

            if 'media' not in track_info:
                raise Exception("No media information found")

            # Get the highest quality MP3 stream URL
            stream_url = None
            for transcoding in track_info['media']['transcodings']:
                if transcoding['format']['protocol'] == 'progressive':
                    stream_url = transcoding['url']
                    break

            if not stream_url:
                raise Exception("No suitable audio stream found")

            # Get the actual media URL
            stream_url = f"{stream_url}?client_id={client_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            r = requests.get(stream_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to get media URL: {r.status_code}")
            
            media_url = r.json()['url']

            # Download the file
            r = requests.get(media_url, headers=headers, stream=True)
            if not r.ok:
                raise Exception(f"Download failed: {r.status_code}")

            temp_file = f"{output_filepath}.mp3"
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            
            # Set metadata
            try:
                audio = ID3(temp_file)
            except:
                audio = ID3()
            audio.add(TIT2(encoding=3, text=song))
            audio.add(TPE1(encoding=3, text=artist))
            audio.save(temp_file)
            
            print(f"Download complete: {temp_file}")
            return temp_file

        except Exception as e:
            print(f"Error downloading track: {e}")
            print("Additional details:")
            print("- Make sure the track is publicly available")
            print("- Verify your internet connection")
            print("- Track might not be available for streaming")
            return None

    def get_track_info(self, url: str) -> Optional[Dict]:
        """Get information about a SoundCloud track."""
        try:
            track_info = self._get_track_info_from_url(url)
            if track_info:
                return format_track_info({
                    'artist': track_info.get('user', {}).get('username', 'Unknown Artist'),
                    'song': track_info['title'],
                    'duration': track_info['duration'] // 1000,  # Convert to seconds
                    'genre': track_info.get('genre', '')
                })
            return None
        except Exception as e:
            print(f"Error getting track info: {e}")
            return None
