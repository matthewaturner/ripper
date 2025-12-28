#!/usr/bin/env python

"""Audio Ripper CLI with support for multiple sources."""
import argparse

from ripper.workflows import SingleSongWorkflow, PlaylistWorkflow, RenameFilesWorkflow, PlaylistImportWorkflow, RepairTrackWorkflow


def main():
    """Main entry point for the audio ripper CLI."""
    parser = argparse.ArgumentParser(
        prog='ripper',
        description='Audio Ripper with multiple source support'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Single song download
    song_parser = subparsers.add_parser('song', help='Download a single song')
    song_parser.add_argument('-a', '--artist', help='Artist name')
    song_parser.add_argument('-s', '--song', help='Song name')
    song_parser.add_argument('--source', choices=['youtube', 'soundcloud'], help='Preferred source')
    
    # Playlist download
    playlist_parser = subparsers.add_parser('playlist', help='Download all songs from a Spotify playlist')
    playlist_parser.add_argument('--uri', required=True, help='Spotify playlist URI (spotify:playlist:ID)')
    playlist_parser.add_argument('--source', choices=['youtube', 'soundcloud'], 
                                help='Preferred source (default: soundcloud)')
    playlist_parser.add_argument('--dir', help='Directory to save downloaded files (default: ~/Downloads)')
    
    # Rename files to include Spotify track IDs
    rename_parser = subparsers.add_parser('rename', help='Rename existing files to include Spotify track IDs')
    rename_parser.add_argument('--directory', help='Directory containing files to rename (default: ~/Downloads)')
    
    # Playlist import - sync local directory with Spotify playlist
    import_parser = subparsers.add_parser('playlist-import', help='Sync Spotify playlist with local directory')
    import_parser.add_argument('--uri', required=True, help='Spotify playlist URI (spotify:playlist:ID)')
    import_parser.add_argument('--dir', required=True, help='Directory containing local track files')
    
    # Repair - re-download a specific track by filename
    repair_parser = subparsers.add_parser('repair', help='Repair/re-download a track by filename')
    repair_parser.add_argument('filename', help='Filename to repair (must include Spotify ID: "Song - Artist {spotify_id}.mp3")')
    repair_parser.add_argument('--source', choices=['youtube', 'soundcloud'], help='Preferred source')
    repair_parser.add_argument('--dir', help='Directory containing the file (default: ~/Downloads)')
    
    args = parser.parse_args()
    
    # Route to appropriate workflow
    if not args.command or args.command == 'song':
        workflow = SingleSongWorkflow()
        workflow.run(args)
    elif args.command == 'playlist':
        workflow = PlaylistWorkflow(downloads_dir=getattr(args, 'dir', None))
        workflow.run(args)
    elif args.command == 'rename':
        workflow = RenameFilesWorkflow()
        workflow.run(args)
    elif args.command == 'repair':
        workflow = RepairTrackWorkflow()
        workflow.run(args)
    elif args.command == 'playlist-import':
        workflow = PlaylistImportWorkflow()
        workflow.run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
