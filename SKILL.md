---
name: Ripper CLI
description: CLI capable of downloading audio files from youtube or soundcloud.
---

# Ripper CLI

```
usage: ripper [-h] {song,playlist,rename,playlist-import,repair} ...

Audio Ripper with multiple source support

positional arguments:
  {song,playlist,rename,playlist-import,repair}
                        Commands
    song                Download a single song
    playlist            Download all songs from a Spotify playlist
    rename              Rename existing files to include Spotify track IDs
    playlist-import     Sync Spotify playlist with local directory
    repair              Repair/re-download a track by file path

options:
  -h, --help            show this help message and exit
```
