"""SoundCloud audio source implementation."""
import os
import json
import re
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import sclib
import requests
import m3u8
from urllib.parse import quote
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            r = requests.get('https://soundcloud.com', headers=headers)
            if not r.ok:
                raise Exception("Failed to fetch SoundCloud homepage")

            script_urls = re.findall(r'<script crossorigin src="([^"]+)"></script>', r.text)
            
            for script_url in script_urls:
                if not script_url.startswith('http'):
                    script_url = 'https://soundcloud.com' + script_url
                
                r = requests.get(script_url, headers=headers)
                if not r.ok:
                    continue

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
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            client_id = self._get_client_id()
            if not client_id:
                raise Exception("Could not obtain valid client ID")

            resolve_url = f"https://api-v2.soundcloud.com/resolve?url={url}&client_id={client_id}"
            r = requests.get(resolve_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to resolve URL: {r.status_code}")
            
            track_data = r.json()
            if not track_data or 'id' not in track_data:
                raise Exception("Could not get track ID")
            
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
            
            encoded_query = quote(query)
            url = f"https://api-v2.soundcloud.com/search/tracks?q={encoded_query}&client_id={client_id}&limit={max_results}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
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

    def _download_hls_stream(self, stream_url: str, temp_file: str, headers: dict) -> bool:
        """Download an HLS stream to a file."""
        try:
            # Get the HLS playlist URL
            r = requests.get(stream_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to get playlist URL: {r.status_code}")

            playlist_url = r.json().get('url')
            if not playlist_url:
                raise Exception("No playlist URL found")

            # Parse the M3U8 playlist
            playlist = m3u8.load(playlist_url)
            if not playlist.segments:
                raise Exception("No segments found in playlist")

            # Download and concatenate all segments
            with open(temp_file, 'wb') as outfile:
                for segment in playlist.segments:
                    r = requests.get(segment.absolute_uri, headers=headers)
                    if r.ok:
                        outfile.write(r.content)
            return True

        except Exception as e:
            print(f"Error downloading HLS stream: {e}")
            return False

    def _download_progressive_stream(self, stream_url: str, temp_file: str, headers: dict) -> bool:
        """Download a progressive stream to a file."""
        try:
            r = requests.get(stream_url, headers=headers)
            if not r.ok:
                raise Exception(f"Failed to get media URL: {r.status_code}")

            media_url = r.json().get('url')
            if not media_url:
                raise Exception("No media URL found")

            r = requests.get(media_url, headers=headers, stream=True)
            if not r.ok:
                raise Exception(f"Download failed: {r.status_code}")

            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            return True

        except Exception as e:
            print(f"Error downloading progressive stream: {e}")
            return False

    def download_track(self, url: str, artist: str, song: str, output_path: Optional[str] = None) -> Optional[str]:
        """Download a track from SoundCloud."""
        if output_path is None:
            output_path = self.downloads_dir

        try:
            track_info = self._get_track_info_from_url(url)
            if not track_info:
                raise Exception("Could not get track info")

            output_filename = f"{song} - {artist}"
            output_filepath = os.path.join(output_path, output_filename)
            temp_file = f"{output_filepath}.mp3"
            
            print(f"\nDownloading: {track_info['title']}")
            
            client_id = self._get_client_id()
            if not client_id:
                raise Exception("Could not obtain valid client ID")

            if 'media' not in track_info:
                raise Exception("No media information found")

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            # Try to get a stream URL, first progressive then HLS
            stream_url = None
            protocol = None

            for transcoding in track_info['media']['transcodings']:
                if transcoding['format']['protocol'] == 'progressive':
                    stream_url = transcoding['url']
                    protocol = 'progressive'
                    break
                elif transcoding['format']['protocol'] == 'hls':
                    stream_url = transcoding['url']
                    protocol = 'hls'

            if not stream_url:
                raise Exception("No suitable audio stream found")

            # Add client ID to stream URL
            stream_url = f"{stream_url}?client_id={client_id}"

            # Download based on protocol
            success = False
            if protocol == 'progressive':
                success = self._download_progressive_stream(stream_url, temp_file, headers)
            elif protocol == 'hls':
                success = self._download_hls_stream(stream_url, temp_file, headers)

            if not success:
                raise Exception("Failed to download audio stream")

            # Set metadata
            try:
                # Try to load existing ID3 tag or create new
                try:
                    audio = ID3(temp_file)
                except:
                    audio = ID3()

                # Set artist and title
                audio.add(TIT2(encoding=3, text=song))
                audio.add(TPE1(encoding=3, text=artist))
                audio.save(temp_file)
            except Exception as e:
                print(f"Warning: Could not set metadata: {e}")
                # Continue anyway since the file is downloaded

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
