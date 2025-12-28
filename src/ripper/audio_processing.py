"""Audio processing utilities for re-encoding and format conversion."""
import os
import subprocess
import tempfile

from ripper.config import FFMPEG_AUDIO_CODEC, FFMPEG_AUDIO_BITRATE, FFMPEG_TIMEOUT


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
