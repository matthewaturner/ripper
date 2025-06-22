"""YouTube audio source implementation."""
import os
from pathlib import Path
from typing import List, Dict, Optional
import eyed3

import yt_dlp
from googleapiclient.discovery import build

from ..base import AudioSource

class YouTubeSource(AudioSource):
    """YouTube implementation of AudioSource."""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YouTube API key not found in environment")
            
        self.ffmpeg_path = os.getenv('FFMPEG_PATH')
        if not self.ffmpeg_path:
            raise ValueError("FFMPEG_PATH not found in environment")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.downloads_dir = str(Path.home() / "Downloads")

    def search_tracks(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for YouTube videos matching query."""
        try:
            response = self.youtube.search().list(
                q=query,
                part='snippet',
                maxResults=max_results,
                type='video'
            ).execute()

            video_ids = [item['id']['videoId'] for item in response['items']]
            
            details = self.youtube.videos().list(
                part='contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()

            results = []
            for search_item, detail_item in zip(response['items'], details['items']):
                results.append({
                    'id': search_item['id']['videoId'],
                    'title': search_item['snippet']['title'],
                    'channel': search_item['snippet']['channelTitle'],
                    'duration': detail_item['contentDetails']['duration'],
                    'views': detail_item['statistics']['viewCount'],
                    'url': f"https://www.youtube.com/watch?v={search_item['id']['videoId']}"
                })
            
            return results
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def download_track(self, url: str, artist: str, song: str, output_path: Optional[str] = None) -> Optional[str]:
        """Download audio from YouTube video."""
        try:
            if output_path is None:
                output_path = self.downloads_dir

            # Create output filename
            output_filename = f"{song} - {artist}"
            output_path = os.path.join(output_path, output_filename)

            # Basic yt-dlp options with ffmpeg path
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': f'{output_path}.%(ext)s',
                'ffmpeg_location': self.ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                final_path = f"{output_path}.mp3"
                
                # Add metadata
                audio = eyed3.load(final_path)
                if audio:
                    if not audio.tag:
                        audio.initTag()
                    audio.tag.artist = artist
                    audio.tag.title = song
                    audio.tag.save()
                
                return final_path

        except Exception as e:
            print(f"Download failed: {e}")
            return None
