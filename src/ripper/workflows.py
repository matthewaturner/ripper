"""Workflow implementations for single song and playlist downloads."""
import argparse
from typing import Optional

from ripper.sources import AudioRipper
from ripper.audio_processing import reencode_mp3
from ripper.file_manager import file_exists, get_expected_filepath
from ripper.ui import display_search_results, display_spotify_track_info, get_user_choice
from ripper.utils.track_matching import find_best_match
from ripper.config import DEFAULT_PLAYLIST_SOURCE


class SingleSongWorkflow:
    """Handles the workflow for downloading a single song."""
    
    def __init__(self):
        self.ripper = AudioRipper()
    
    def run(self, args: argparse.Namespace) -> None:
        """Execute single song download workflow.
        
        Args:
            args: Parsed command line arguments
        """
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
        results = self.ripper.search_all_sources(query, preferred_source=args.source)
        
        if not results:
            print("No results found in any source")
            return

        # Display results and get user choice
        result_map = display_search_results(results)
        
        choice = get_user_choice(len(result_map))
        if choice is None:
            print("Skipping download...")
            return

        # Get the chosen result and its source
        source, selected_track = result_map[choice]
        print(f"\nDownloading from {source.upper()}: {selected_track['title']}")
        
        # Download and re-encode the track
        self._download_and_reencode(source, selected_track, artist, song)
    
    def _download_and_reencode(self, source: str, track: dict, artist: str, song: str) -> None:
        """Download a track and re-encode it.
        
        Args:
            source: Source to download from
            track: Track metadata dictionary
            artist: Artist name
            song: Song name
        """
        output_file = self.ripper.download_track(source, track['url'], artist, song)
        
        if output_file:
            print(f"\nDownload complete! File saved to: {output_file}")
            print("Re-encoding file for compatibility...")
            if reencode_mp3(output_file):
                print("Re-encoding successful!")
            else:
                print("Warning: Re-encoding failed, file may have compatibility issues")
        else:
            print("\nFailed to download audio")


class PlaylistWorkflow:
    """Handles the workflow for downloading an entire playlist."""
    
    def __init__(self):
        self.ripper = AudioRipper()
    
    def run(self, args: argparse.Namespace) -> None:
        """Execute playlist download workflow.
        
        Args:
            args: Parsed command line arguments
        """
        if not args.uri:
            print("Please provide a Spotify playlist URI (format: spotify:playlist:ID)")
            return
        
        preferred_source = args.source if args.source else DEFAULT_PLAYLIST_SOURCE
        
        try:
            print(f"\nFetching playlist: {args.uri}")
            tracks = self.ripper.get_source('spotify').get_playlist_tracks(args.uri)
            
            if not tracks:
                print("No tracks found in playlist")
                return
            
            total_tracks = len(tracks)
            print(f"Found {total_tracks} tracks in playlist\n")
            
            for i, track in enumerate(tracks, 1):
                self._process_playlist_track(i, total_tracks, track, preferred_source)
                    
        except Exception as e:
            print(f"Error processing playlist: {e}")
    
    def _process_playlist_track(self, index: int, total: int, track: dict, 
                                preferred_source: str) -> None:
        """Process a single track from a playlist.
        
        Args:
            index: Current track number
            total: Total number of tracks
            track: Track metadata from Spotify
            preferred_source: Preferred download source
        """
        print(f"\nProcessing track {index}/{total}")
        print(f"Artist: {track['artist']}")
        print(f"Song: {track['song']}")
        
        # Check if file already exists
        if file_exists(track['artist'], track['song']):
            filename = f"{track['song']} - {track['artist']}.mp3"
            print(f"File already exists, skipping: {filename}")
            print("\n" + "-"*50)
            return
        
        # Search for the song
        query = f"{track['artist']} - {track['song']}"
        results = self.ripper.search_all_sources(query, preferred_source=preferred_source)
        
        if not results:
            print("No results found, skipping...")
            return
        
        # Try to find a match
        selected, used_source = self._find_track_match(
            track, results, preferred_source
        )
        
        if not selected:
            return
        
        # Download and re-encode
        output_file = self.ripper.download_track(
            used_source, 
            selected['url'],
            track['artist'],
            track['song']
        )
        
        if output_file:
            print(f"Downloaded to: {output_file}")
            print("Re-encoding file for compatibility...")
            if reencode_mp3(output_file):
                print("Re-encoding successful!")
            else:
                print("Warning: Re-encoding failed, file may have compatibility issues")
        else:
            print("Download failed, skipping...")
        
        print("\n" + "-"*50)  # Separator between tracks
    
    def _find_track_match(self, track: dict, results: dict, 
                         preferred_source: str) -> tuple[Optional[dict], Optional[str]]:
        """Find best match for a track, using auto-matching or manual selection.
        
        Args:
            track: Spotify track metadata
            results: Search results from multiple sources
            preferred_source: Preferred download source
            
        Returns:
            Tuple of (selected_track, source_name) or (None, None) if skipped
        """
        # Get Spotify metadata for better matching
        spotify_data = self.ripper.get_source('spotify').search_track(
            track['artist'], track['song']
        )
        
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
        
        # If auto-matching failed, fall back to manual selection
        if not selected:
            selected, used_source = self._manual_track_selection(
                spotify_data, results
            )
        
        return selected, used_source
    
    def _manual_track_selection(self, spotify_data: Optional[dict], 
                                results: dict) -> tuple[Optional[dict], Optional[str]]:
        """Let user manually select a track from search results.
        
        Args:
            spotify_data: Spotify track metadata (optional)
            results: Search results from multiple sources
            
        Returns:
            Tuple of (selected_track, source_name) or (None, None) if skipped
        """
        print("\nNo automatic match found, please select manually:")
        
        # Display Spotify track info if available
        if spotify_data:
            display_spotify_track_info(spotify_data)
        
        # Display results from all sources
        result_map = display_search_results(results)
        
        if len(result_map) == 0:
            print("No results found in any source, skipping...")
            return None, None

        # Get user choice
        choice = get_user_choice(len(result_map))
        if choice is None:
            print("Skipping this track...")
            return None, None
        
        used_source, selected = result_map[choice]
        return selected, used_source
