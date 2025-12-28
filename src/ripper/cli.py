#!/usr/bin/env python

"""Audio Ripper CLI with support for multiple sources."""
import argparse

from ripper.workflows import SingleSongWorkflow, PlaylistWorkflow


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
    playlist_parser.add_argument('--output-dir', help='Directory to save downloaded files (default: ~/Downloads)')
    
    args = parser.parse_args()
    
    # Route to appropriate workflow
    if not args.command or args.command == 'song':
        workflow = SingleSongWorkflow()
        workflow.run(args)
    elif args.command == 'playlist':
        workflow = PlaylistWorkflow(downloads_dir=getattr(args, 'output_dir', None))
        workflow.run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
