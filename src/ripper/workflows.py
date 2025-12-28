"""Workflow implementations for single song and playlist downloads."""
import argparse
import os
import re
from typing import Optional
from dotenv import load_dotenv

from ripper.sources import AudioRipper
from ripper.sources.spotify.spotify_source import SpotifySource
from ripper.audio_processing import reencode_mp3
from ripper.file_manager import file_exists, get_expected_filepath
from ripper.ui import display_search_results, display_spotify_track_info, get_user_choice
from ripper.utils.track_matching import find_best_match
from ripper.config import DEFAULT_PLAYLIST_SOURCE, DOWNLOADS_DIR


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
    
    def __init__(self, downloads_dir: Optional[str] = None):
        self.ripper = AudioRipper(downloads_dir=downloads_dir)
        self.downloads_dir = downloads_dir
    
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
            
            # Check for duplicate songs (same title by same artist)
            if not self._check_duplicates(tracks):
                print("\nPlaylist download cancelled.")
                return
            
            for i, track in enumerate(tracks, 1):
                self._process_playlist_track(i, total_tracks, track, preferred_source)
            
            # Check for duplicates in the downloaded files
            print("\n" + "="*50)
            self._check_folder_duplicates()
                    
        except Exception as e:
            print(f"Error processing playlist: {e}")
    
    def _check_duplicates(self, tracks: list[dict]) -> bool:
        """Check for duplicate songs (same title by same artist, case insensitive).
        
        Args:
            tracks: List of track dictionaries from playlist
            
        Returns:
            True if user wants to continue, False otherwise
        """
        # Build a dictionary to track songs by (artist, title) key (case insensitive)
        song_map = {}
        duplicates = []
        
        for track in tracks:
            artist = track['artist'].lower()
            song = track['song'].lower()
            key = (artist, song)
            
            if key in song_map:
                # Found a duplicate
                duplicates.append({
                    'artist': track['artist'],
                    'song': track['song']
                })
            else:
                song_map[key] = track
        
        if duplicates:
            print("\n⚠️  WARNING: Found duplicate songs in playlist!")
            print("The following songs have the same title and artist (may cause issues):\n")
            
            for dup in duplicates:
                print(f"  • {dup['song']} - {dup['artist']}")
            
            print("\nIt may be best to fix these duplicates in your playlist first.")
            response = input("Do you want to continue anyway? (y/n): ").strip().lower()
            
            if response != 'y' and response != 'yes':
                return False
            
            print("\nContinuing with download...\n")
        
        return True
    
    def _check_folder_duplicates(self) -> None:
        """Check for duplicate files in the downloads folder (ignoring Spotify IDs)."""
        dir_path = self.downloads_dir if self.downloads_dir else DOWNLOADS_DIR
        
        if not os.path.exists(dir_path):
            return
        
        # Build a map of base filenames (without Spotify ID) to actual filenames
        file_map = {}
        
        for filename in os.listdir(dir_path):
            if not filename.endswith('.mp3'):
                continue
            
            # Strip out the Spotify ID portion {spotify_id} from the filename
            # Format: "Song - Artist {spotify_id}.mp3" -> "Song - Artist.mp3"
            base_name = re.sub(r'\s*\{[^}]+\}\.mp3$', '.mp3', filename)
            
            if base_name in file_map:
                file_map[base_name].append(filename)
            else:
                file_map[base_name] = [filename]
        
        # Find duplicates
        duplicates = {base: files for base, files in file_map.items() if len(files) > 1}
        
        if duplicates:
            print("\n⚠️  WARNING: Found duplicate files in downloads folder!")
            print("The following files have the same name (ignoring Spotify IDs):\n")
            
            for base_name, files in duplicates.items():
                print(f"  Base name: {base_name}")
                for file in files:
                    print(f"    - {file}")
                print()
            
            print("You may want to review and remove duplicates.")
        else:
            print("\n✓ No duplicate files found in downloads folder.")
    
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
        spotify_track_id = track.get('spotify_track_id')
        if file_exists(track['artist'], track['song'], self.downloads_dir, spotify_track_id):
            if spotify_track_id:
                filename = f"{track['song']} - {track['artist']} {{{spotify_track_id}}}.mp3"
            else:
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
            track['song'],
            spotify_track_id=spotify_track_id
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


class RenameFilesWorkflow:
    """Handles renaming existing files to include Spotify track IDs."""
    
    def __init__(self):
        load_dotenv()
        self.spotify = SpotifySource()
    
    def run(self, args: argparse.Namespace) -> None:
        """Execute file renaming workflow.
        
        Args:
            args: Parsed command line arguments with 'directory' attribute
        """
        directory = args.directory if hasattr(args, 'directory') and args.directory else DOWNLOADS_DIR
        
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return
        
        print(f"\nScanning directory: {directory}")
        
        # Find all .mp3 files without Spotify track IDs
        files_to_rename = []
        for filename in os.listdir(directory):
            if filename.endswith('.mp3') and '{' not in filename:
                files_to_rename.append(filename)
        
        if not files_to_rename:
            print("No files found that need renaming.")
            return
        
        print(f"Found {len(files_to_rename)} file(s) to process.\n")
        
        for index, filename in enumerate(files_to_rename, 1):
            print(f"\n[{index}/{len(files_to_rename)}] Processing: {filename}")
            self._process_file(directory, filename)
    
    def _process_file(self, directory: str, filename: str) -> None:
        """Process a single file to add Spotify track ID.
        
        Args:
            directory: Directory containing the file
            filename: Name of the file to process
        """
        # Parse filename to extract artist and song
        # Expected format: "Song Name - Artist Name.mp3"
        match = re.match(r'^(.+?) - (.+?)\.mp3$', filename)
        if not match:
            print(f"  ⚠ Skipping: Could not parse filename format")
            return
        
        song = match.group(1).strip()
        artist = match.group(2).strip()
        
        print(f"  Song: {song}")
        print(f"  Artist: {artist}")
        
        # Search for track on Spotify
        track_info = self.spotify.search_track(artist, song)
        
        if not track_info:
            print(f"  ✗ Track not found on Spotify")
            return
        
        if 'spotify_track_id' not in track_info:
            print(f"  ✗ No Spotify track ID found")
            return
        
        spotify_track_id = track_info['spotify_track_id']
        print(f"  ✓ Found Spotify ID: {spotify_track_id}")
        
        # Create new filename
        new_filename = f"{song} - {artist} {{{spotify_track_id}}}.mp3"
        
        # Check if file with new name already exists
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_filename)
        
        if os.path.exists(new_path):
            print(f"  ⚠ File already exists with new name, skipping")
            return
        
        # Rename the file
        try:
            os.rename(old_path, new_path)
            print(f"  ✓ Renamed to: {new_filename}")
        except Exception as e:
            print(f"  ✗ Error renaming file: {e}")


class PlaylistImportWorkflow:
    """Handles syncing a local directory with a Spotify playlist."""
    
    def __init__(self):
        load_dotenv()
        self.spotify = SpotifySource()
    
    def run(self, args: argparse.Namespace) -> None:
        """Execute playlist import workflow.
        
        Args:
            args: Parsed command line arguments with 'uri' and 'dir' attributes
        """
        if not args.uri:
            print("Please provide a Spotify playlist URI (format: spotify:playlist:ID)")
            return
        
        if not args.dir:
            print("Please provide an input directory with --dir")
            return
        
        input_dir = os.path.expanduser(args.dir)
        if not os.path.exists(input_dir):
            print(f"Directory not found: {input_dir}")
            return
        
        print(f"\nFetching playlist information...")
        playlist_info = self.spotify.get_playlist_info(args.uri)
        if not playlist_info:
            print("Failed to fetch playlist information")
            return
        
        print(f"Playlist: {playlist_info['name']}")
        print(f"Owner: {playlist_info['owner']}")
        
        print(f"\nFetching playlist tracks from Spotify...")
        spotify_tracks = self.spotify.get_playlist_tracks(args.uri)
        
        if spotify_tracks is None:
            print("Failed to fetch playlist tracks")
            return
        
        # Build set of Spotify track IDs
        spotify_track_ids = {track['spotify_track_id'] for track in spotify_tracks if 'spotify_track_id' in track}
        print(f"Found {len(spotify_track_ids)} tracks in Spotify playlist")
        
        print(f"\nScanning directory: {input_dir}")
        local_track_ids = self._scan_directory_for_track_ids(input_dir)
        print(f"Found {len(local_track_ids)} tracks in local directory")
        
        # Calculate differences
        tracks_to_add = local_track_ids - spotify_track_ids
        tracks_to_remove = spotify_track_ids - local_track_ids
        
        # Display the diff
        self._display_diff(tracks_to_add, tracks_to_remove)
        
        if not tracks_to_add and not tracks_to_remove:
            print("\n✓ Playlist and directory are already in sync!")
            return
        
        # Ask for confirmation
        response = input("\nProceed with these changes? (y/n): ").strip().lower()
        if response != 'y':
            print("Operation cancelled")
            return
        
        # Perform the sync
        success = self._sync_playlist(args.uri, tracks_to_add, tracks_to_remove)
        
        if success:
            print("\n✓ Playlist sync completed successfully!")
        else:
            print("\n✗ Playlist sync encountered errors")
    
    def _scan_directory_for_track_ids(self, directory: str) -> set:
        """Scan directory for files with Spotify track IDs in their names.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Set of Spotify track IDs found in filenames
        """
        track_ids = set()
        
        for filename in os.listdir(directory):
            # Match pattern: "artist - song {spotify_track_id}.extension"
            match = re.search(r'\{([a-zA-Z0-9]+)\}', filename)
            if match:
                track_id = match.group(1)
                track_ids.add(track_id)
        
        return track_ids
    
    def _display_diff(self, tracks_to_add: set, tracks_to_remove: set) -> None:
        """Display the difference between local directory and Spotify playlist.
        
        Args:
            tracks_to_add: Track IDs to add to playlist
            tracks_to_remove: Track IDs to remove from playlist
        """
        print("\n" + "="*60)
        print("PLAYLIST SYNC PREVIEW")
        print("="*60)
        
        if tracks_to_add:
            print(f"\n✚ TRACKS TO ADD TO PLAYLIST ({len(tracks_to_add)}):")
            for track_id in sorted(tracks_to_add):
                track_info = self.spotify.get_track_by_id(track_id)
                if track_info:
                    print(f"  • {track_info['artist']} - {track_info['song']}")
                else:
                    print(f"  • [Unknown track: {track_id}]")
        
        if tracks_to_remove:
            print(f"\n✖ TRACKS TO REMOVE FROM PLAYLIST ({len(tracks_to_remove)}):")
            for track_id in sorted(tracks_to_remove):
                track_info = self.spotify.get_track_by_id(track_id)
                if track_info:
                    print(f"  • {track_info['artist']} - {track_info['song']}")
                else:
                    print(f"  • [Unknown track: {track_id}]")
        
        print("\n" + "="*60)
    
    def _sync_playlist(self, playlist_uri: str, tracks_to_add: set, 
                       tracks_to_remove: set) -> bool:
        """Sync the playlist with the local directory.
        
        Args:
            playlist_uri: Spotify playlist URI
            tracks_to_add: Track IDs to add to playlist
            tracks_to_remove: Track IDs to remove from playlist
            
        Returns:
            True if all operations succeeded, False otherwise
        """
        success = True
        
        if tracks_to_remove:
            print(f"\nRemoving {len(tracks_to_remove)} track(s) from playlist...")
            if self.spotify.remove_tracks_from_playlist(playlist_uri, list(tracks_to_remove)):
                print("✓ Successfully removed tracks")
            else:
                print("✗ Failed to remove some tracks")
                success = False
        
        if tracks_to_add:
            print(f"\nAdding {len(tracks_to_add)} track(s) to playlist...")
            if self.spotify.add_tracks_to_playlist(playlist_uri, list(tracks_to_add)):
                print("✓ Successfully added tracks")
            else:
                print("✗ Failed to add some tracks")
                success = False
        
        return success


class RepairTrackWorkflow:
    """Handles repairing/re-downloading a single track by filename."""
    
    def __init__(self, downloads_dir: Optional[str] = None):
        load_dotenv()
        self.downloads_dir = downloads_dir
        self.ripper = AudioRipper(downloads_dir=downloads_dir)
        self.spotify = SpotifySource()
    
    def run(self, args: argparse.Namespace) -> None:
        """Execute repair workflow for a single track.
        
        Args:
            args: Parsed command line arguments with 'filename' attribute
        """
        if not args.filename:
            print("Please provide a filename to repair")
            return
        
        filename = args.filename
        
        # Extract Spotify track ID from filename
        # Format: "Song - Artist {spotify_id}.mp3"
        match = re.search(r'\{([a-zA-Z0-9]+)\}', filename)
        if not match:
            print(f"Error: No Spotify track ID found in filename")
            print(f"Expected format: 'Song - Artist {{spotify_id}}.mp3'")
            print(f"The repair command requires a Spotify track ID to look up track metadata.")
            return
        
        spotify_track_id = match.group(1)
        
        # Look up track metadata from Spotify
        print(f"\nLooking up track on Spotify...")
        print(f"  Spotify ID: {spotify_track_id}")
        
        track_info = self.spotify.get_track_by_id(spotify_track_id)
        if not track_info:
            print(f"Error: Could not find track on Spotify with ID: {spotify_track_id}")
            return
        
        artist = track_info['artist']
        song = track_info['song']
        
        print(f"\nRepairing track:")
        print(f"  Artist: {artist}")
        print(f"  Song: {song}")
        print(f"  Spotify ID: {spotify_track_id}")
        
        # Determine file path
        # If filename is a full path, use it directly
        # Otherwise, construct path from downloads_dir and filename
        if os.path.isabs(filename) or filename.startswith('~'):
            file_path = os.path.expanduser(filename)
            downloads_dir = os.path.dirname(file_path)
            # Update the ripper to use this directory
            self.ripper = AudioRipper(downloads_dir=downloads_dir)
        else:
            downloads_dir = getattr(args, 'dir', None) or self.downloads_dir or DOWNLOADS_DIR
            file_path = os.path.join(downloads_dir, filename)
            # Update the ripper to use this directory if different
            if self.ripper.downloads_dir != downloads_dir:
                self.ripper = AudioRipper(downloads_dir=downloads_dir)
        
        if not os.path.exists(file_path):
            print(f"\nWarning: File not found at expected location:")
            print(f"  {file_path}")
            response = input("Continue with download anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("Repair cancelled")
                return
        else:
            print(f"\nFound existing file:")
            print(f"  {file_path}")
            response = input("This will be overwritten. Continue? (y/n): ").strip().lower()
            if response != 'y':
                print("Repair cancelled")
                return
        
        # Search for the track
        query = f"{artist} - {song}"
        print(f"\nSearching for: {query}")
        
        preferred_source = getattr(args, 'source', None)
        results = self.ripper.search_all_sources(query, preferred_source=preferred_source)
        
        if not results:
            print("No results found in any source")
            return
        
        # Always show results and let user choose (never auto-match)
        print("\nPlease select the correct version to download:")
        result_map = display_search_results(results)
        
        if len(result_map) == 0:
            print("No results found in any source")
            return
        
        choice = get_user_choice(len(result_map))
        if choice is None:
            print("Repair cancelled")
            return
        
        # Get the chosen result and its source
        source, selected_track = result_map[choice]
        print(f"\nDownloading from {source.upper()}: {selected_track['title']}")
        
        # Delete existing file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed existing file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not remove existing file: {e}")
        
        # Download and re-encode the track
        output_file = self.ripper.download_track(
            source, 
            selected_track['url'], 
            artist, 
            song,
            spotify_track_id=spotify_track_id
        )
        
        if output_file:
            print(f"\nDownload complete! File saved to: {output_file}")
            print("Re-encoding file for compatibility...")
            if reencode_mp3(output_file):
                print("Re-encoding successful!")
                print("\n✓ Track repair completed successfully!")
            else:
                print("Warning: Re-encoding failed, file may have compatibility issues")
        else:
            print("\nFailed to download audio")
