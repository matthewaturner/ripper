import os
from pathlib import Path
from typing import List, Dict
import yt_dlp
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeRipper:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YouTube API key not found. Please set it in .env file")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.downloads_dir = str(Path.home() / "Downloads")

    def search_videos(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for videos matching the query."""
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                maxResults=max_results,
                type='video'
            ).execute()

            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get additional video details like duration and view count
            videos_response = self.youtube.videos().list(
                part='contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()

            # Combine search results with video details
            results = []
            for search_item, video_item in zip(search_response['items'], videos_response['items']):
                results.append({
                    'id': search_item['id']['videoId'],
                    'title': search_item['snippet']['title'],
                    'channel': search_item['snippet']['channelTitle'],
                    'duration': video_item['contentDetails']['duration'],
                    'views': video_item['statistics']['viewCount'],
                    'url': f"https://www.youtube.com/watch?v={search_item['id']['videoId']}"
                })
            
            return results
        except Exception as e:
            print(f"Error searching videos: {e}")
            return []

    def download_audio(self, video_url: str, output_path: str = None) -> str:
        """Download audio from YouTube video and save as MP3."""
        if output_path is None:
            output_path = self.downloads_dir

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                return os.path.join(output_path, f"{info['title']}.mp3")
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None

def format_duration(duration: str) -> str:
    """Convert YouTube duration format (ISO 8601) to readable format."""
    import re
    from datetime import timedelta

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

def main():
    ripper = YouTubeRipper()
    
    # Get search query from user
    query = input("Enter search term: ").strip()
    if not query:
        print("Search term cannot be empty")
        return

    # Search for videos
    print("\nSearching for videos...")
    results = ripper.search_videos(query)
    
    if not results:
        print("No results found")
        return

    # Display results
    print("\nSearch Results:")
    for i, video in enumerate(results, 1):
        duration = format_duration(video['duration'])
        views = format_views(video['views'])
        print(f"\n{i}. {video['title']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Duration: {duration} | {views}")

    # Get user choice
    while True:
        try:
            choice = int(input("\nEnter number to download (1-5): "))
            if 1 <= choice <= len(results):
                break
            print(f"Please enter a number between 1 and {len(results)}")
        except ValueError:
            print("Please enter a valid number")

    # Download the chosen video's audio
    selected_video = results[choice - 1]
    print(f"\nDownloading audio from: {selected_video['title']}")
    output_file = ripper.download_audio(selected_video['url'])
    
    if output_file:
        print(f"\nDownload complete! File saved to: {output_file}")
    else:
        print("\nFailed to download audio")

if __name__ == "__main__":
    main()
