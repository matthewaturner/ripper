"""Sources package for audio download sources."""
from .youtube.youtube_source import YouTubeSource
from .spotify.spotify_source import SpotifySource
from .soundcloud.soundcloud_source import SoundCloudSource

__all__ = ['YouTubeSource', 'SpotifySource', 'SoundCloudSource']
