"""Audio processing utilities for re-encoding and format conversion."""
import json
import os
import subprocess
import tempfile
from typing import Optional, Dict, Any

from ripper.config import FFMPEG_AUDIO_CODEC, FFMPEG_AUDIO_BITRATE, FFMPEG_TIMEOUT


def detect_audio_format(file_path: str) -> Optional[Dict[str, Any]]:
    """Detect audio file format, codec, bitrate, and sample rate using ffprobe.
    
    Args:
        file_path: Path to the audio file to analyze
        
    Returns:
        Dictionary with format info or None if detection fails:
        {
            'codec': str,           # e.g., 'mp3', 'aac', 'flac'
            'bitrate': int,         # bits per second
            'sample_rate': int,     # Hz (e.g., 44100, 48000)
            'channels': int,        # 1 (mono) or 2 (stereo)
            'duration': float,      # seconds
            'bitrate_mode': str     # 'cbr' or 'vbr' (if detectable)
        }
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )
        
        if result.returncode != 0:
            return None
            
        data = json.loads(result.stdout)
        
        # Find the audio stream
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_stream = stream
                break
                
        if not audio_stream:
            return None
            
        format_info = data.get('format', {})
        
        # Determine bitrate mode if possible (MP3 specific)
        bitrate_mode = 'unknown'
        codec = audio_stream.get('codec_name', '').lower()
        if codec == 'mp3':
            # Check for VBR indicators in tags
            tags = format_info.get('tags', {})
            encoder = tags.get('encoder', '').lower()
            if 'vbr' in encoder or 'lame' in encoder:
                bitrate_mode = 'vbr'
            else:
                bitrate_mode = 'cbr'
        
        return {
            'codec': codec,
            'bitrate': int(audio_stream.get('bit_rate', 0)),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
            'duration': float(format_info.get('duration', 0)),
            'bitrate_mode': bitrate_mode
        }
        
    except Exception as e:
        print(f"Warning: Failed to detect audio format: {e}")
        return None


def check_rekordbox_compatible(format_info: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """Check if audio file is compatible with rekordbox without re-encoding.
    
    Rekordbox supports:
    - MP3: All bitrates (CBR/VBR), 44.1/48 kHz sample rate
    - AAC/M4A: Most configurations
    - WAV, AIFF, FLAC: Lossless formats
    
    Common incompatibility issues:
    - Corrupted/invalid headers
    - Unsupported codecs (e.g., Opus, Vorbis)
    - Non-standard sample rates (rare)
    
    Args:
        format_info: Dictionary from detect_audio_format()
        
    Returns:
        Tuple of (is_compatible, reason_if_incompatible)
    """
    if not format_info:
        return False, "Unable to detect format"
    
    codec = format_info.get('codec', '').lower()
    sample_rate = format_info.get('sample_rate', 0)
    bitrate = format_info.get('bitrate', 0)
    
    # Supported codecs
    supported_codecs = {'mp3', 'aac', 'wav', 'flac', 'aiff', 'alac', 'pcm_s16le', 'pcm_s24le'}
    
    if codec not in supported_codecs:
        return False, f"Unsupported codec: {codec}"
    
    # Check for suspiciously low quality (likely corrupted or partial download)
    if codec in {'mp3', 'aac'} and bitrate < 96000:
        return False, f"Bitrate too low: {bitrate // 1000}kbps (minimum 96kbps recommended)"
    
    # Sample rate check (44.1 kHz and 48 kHz are standard; others may work but are uncommon)
    if sample_rate not in {44100, 48000}:
        # Don't fail, but note it might need re-encoding
        return False, f"Non-standard sample rate: {sample_rate} Hz (rekordbox prefers 44.1/48 kHz)"
    
    # File is compatible
    return True, None


def reencode_mp3(file_path: str) -> bool:
    """Re-encode MP3 file to ensure compatibility.
    
    Args:
        file_path: Path to the MP3 file to re-encode
        
    Returns:
        True if re-encoding succeeded, False otherwise
    """
    try:
        # Create a temporary file in the same directory
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', dir=os.path.dirname(file_path))
        os.close(temp_fd)
        
        # Run ffmpeg to re-encode
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-c:a', FFMPEG_AUDIO_CODEC,
            '-b:a', FFMPEG_AUDIO_BITRATE,
            '-y',  # Overwrite output file without asking
            temp_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=FFMPEG_TIMEOUT
        )
        
        if result.returncode == 0:
            # Replace original file with re-encoded version
            os.replace(temp_path, file_path)
            return True
        else:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
    except Exception as e:
        print(f"Warning: Failed to re-encode file: {e}")
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False
