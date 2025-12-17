#!/usr/bin/env python

"""Audio Ripper CLI with support for multiple sources."""
import os
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from sources import YouTubeSource, SpotifySource, SoundCloudSource
from utils.formatting import format_duration, format_views
from utils.track_matching import find_best_match

class AudioRipper:
    """Main class for handling audio ripping from multiple sources."""
    
    def __init__(self):
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
            self.sources[source] = self.source_classes[source]()
            
        return self.sources[source]

    def search_source(self, source: str, query: str, max_results: int = 5) -> List[Dict]:
        """Search a specific source for tracks."""
        try:
            return self.get_source(source).search_tracks(query, max_results)
        except Exception as e:
            print(f"Error searching {source}: {e}")
            return []

    def search_all_sources(self, query: str, max_results: int = 5, preferred_source: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Search across available sources, prioritizing preferred source."""
        results = {}
        
        # Search all sources (except Spotify which is for playlists only)
        for source in self.source_classes:
            if source != 'spotify':  # Skip Spotify as it's for playlists only
                source_results = self.search_source(source, query, max_results)
                if source_results:
                    results[source] = source_results
            
        return results

    def download_track(self, source: str, url: str, artist: str, song: str) -> Optional[str]:
        """Download a track using the specified source."""
        try:
            return self.get_source(source).download_track(url, artist, song)
        except Exception as e:
            print(f"Error downloading from {source}: {e}")
            return None

def handle_single_song(args: argparse.Namespace) -> None:
    """Handle single song download."""
    ripper = AudioRipper()
    
    # Get artist and song from arguments or prompt
    artist = args.artist if args.artist else input("Enter artist name: ").strip()
    song = args.song if args.song else input("Enter song name: ").strip()
    
    if not artist or not song:
        print("Both artist and song name are required")
        return

    # Create search query
    query = f"{artist} - {song}"
    print(f"\nSearching for: {query}")
    
    # Search across sources, prioritizing preferred source if specified
    results = ripper.search_all_sources(query, preferred_source=args.source)
    
    if not results:
        print("No results found in any source")
        return

    # Display results by source
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

    # Get user choice
    while True:
        try:
            choice = int(input(f"\nEnter number to download (1-{total_results}, or -1 to skip): "))
            if choice == -1:
                print("Skipping download...")
                return
            if 1 <= choice <= total_results:
                break
            print(f"Please enter a number between 1 and {total_results}, or -1 to skip")
        except ValueError:
            print("Please enter a valid number")

    # Get the chosen result and its source
    source, selected_track = result_map[choice]
    print(f"\nDownloading from {source.upper()}: {selected_track['title']}")
    
    # Download the track
    output_file = ripper.download_track(source, selected_track['url'], artist, song)
    
    if output_file:
        print(f"\nDownload complete! File saved to: {output_file}")
    else:
        print("\nFailed to download audio")

def export_playlist(args: argparse.Namespace) -> None:
    """Export Spotify playlist to CSV."""
    if not args.uri:
        print("Please provide a Spotify playlist URI (format: spotify:playlist:ID)")
        return
    
    if not args.output:
        print("Please provide an output CSV file path")
        return
    
    try:
        ripper = AudioRipper()
        print(f"\nFetching playlist: {args.uri}")
        tracks = ripper.get_source('spotify').get_playlist_tracks(args.uri)
        
        if not tracks:
            print("No tracks found in playlist")
            return
        
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['artist', 'song', 'album', 'year', 'duration'], 
                                   quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(tracks)
        
        print(f"\nExported {len(tracks)} tracks to {args.output}")
        
    except Exception as e:
        print(f"Error exporting playlist: {e}")

def rip_from_csv(args: argparse.Namespace) -> None:
    """Download songs from CSV file."""
    if not args.input:
        print("Please provide an input CSV file")
        return
    
    if not os.path.exists(args.input):
        print(f"CSV file not found: {args.input}")
        return
    
    ripper = AudioRipper()
    preferred_source = args.source if args.source else 'soundcloud'  # Default to SoundCloud
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            total_tracks = sum(1 for _ in reader)  # Count rows
            f.seek(0)  # Reset file pointer
            next(reader)  # Skip header row
            
            for i, track in enumerate(reader, 1):
                print(f"\nProcessing track {i}/{total_tracks}")
                print(f"Artist: {track['artist']}")
                print(f"Song: {track['song']}")
                
                # Search for the song
                query = f"{track['artist']} - {track['song']}"
                results = ripper.search_all_sources(query, preferred_source=preferred_source)
                
                if not results:
                    print("No results found, skipping...")
                    continue
                
                # Get Spotify metadata for better matching
                spotify_ripper = AudioRipper()
                spotify_data = spotify_ripper.get_source('spotify').search_track(track['artist'], track['song'])
                
                # Try auto-matching if we have Spotify data
                selected = None
                used_source = preferred_source
                
                if spotify_data:
                    print("Using Spotify metadata for matching...")
                    # Try preferred source first
                    if preferred_source in results:
                        selected = find_best_match(spotify_data, results[preferred_source], preferred_source)
                        if selected:
                            print(f"Found good match in {preferred_source}!")
                    
                    # If no good match in preferred source, try others
                    if not selected:
                        for source, source_results in results.items():
                            if source != preferred_source:
                                selected = find_best_match(spotify_data, source_results, source)
                                if selected:
                                    used_source = source
                                    print(f"Found good match in {source}!")
                                    break
                
                # If auto-matching failed or no Spotify data, fall back to manual selection
                if not selected:
                    print("\nNo automatic match found, please select manually:")
                    
                    # Display Spotify track info if available
                    if spotify_data:
                        spotify_duration = format_duration(spotify_data['duration'])
                        print(f"\nSpotify Track Info:")
                        print(f"   {spotify_data['artist']} - {spotify_data['song']}")
                        print(f"   Duration: {spotify_duration}")
                    
                    # Display results from all sources
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
                    
                    if total_results == 0:
                        print("No results found in any source, skipping...")
                        continue

                    # Get user choice
                    while True:
                        try:
                            choice = int(input(f"\nEnter number to download (1-{total_results}, or -1 to skip): "))
                            if choice == -1:
                                print("Skipping this track...")
                                selected = None
                                break
                            if 1 <= choice <= total_results:
                                used_source, selected = result_map[choice]
                                break
                            print(f"Please enter a number between 1 and {total_results}, or -1 to skip")
                        except ValueError:
                            print("Please enter a valid number")
                    
                    if not selected:
                        continue
                output_file = ripper.download_track(
                    used_source, 
                    selected['url'],
                    track['artist'],
                    track['song']
                )
                
                if output_file:
                    print(f"Downloaded to: {output_file}")
                else:
                    print("Download failed, skipping...")
                
                print("\n" + "-"*50)  # Separator between tracks
                
    except Exception as e:
        print(f"Error processing CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Audio Ripper with multiple source support')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Single song download
    song_parser = subparsers.add_parser('song', help='Download a single song')
    song_parser.add_argument('-a', '--artist', help='Artist name')
    song_parser.add_argument('-s', '--song', help='Song name')
    song_parser.add_argument('--source', choices=['youtube', 'soundcloud'], help='Preferred source')
    
    # Playlist export
    playlist_export_parser = subparsers.add_parser('playlist', help='Playlist operations')
    playlist_subparsers = playlist_export_parser.add_subparsers(dest='playlist_command', help='Playlist commands')
    
    export_parser = playlist_subparsers.add_parser('export', help='Export Spotify playlist to CSV')
    export_parser.add_argument('--uri', help='Spotify playlist URI (spotify:playlist:ID)')
    export_parser.add_argument('--output', help='Output CSV file path')
    
    rip_parser = playlist_subparsers.add_parser('rip', help='Download songs from CSV')
    rip_parser.add_argument('--input', help='Input CSV file path')
    rip_parser.add_argument('--source', choices=['youtube', 'soundcloud'], 
                           help='Preferred source (default: soundcloud)')
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to single song if no command specified
        handle_single_song(args)
    elif args.command == 'song':
        handle_single_song(args)
    elif args.command == 'playlist':
        if args.playlist_command == 'export':
            export_playlist(args)
        elif args.playlist_command == 'rip':
            rip_from_csv(args)
        else:
            print("Please specify a playlist command (export or rip)")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
