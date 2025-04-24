
import subprocess
from pathlib import Path

class MediaConverter:
    @staticmethod
    def convert_video_to_audio(input_path: str, output_path: str) -> str:
        try:
            subprocess.run(['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libmp3lame', output_path], check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error al convertir el video: {str(e)}")
