import os
from pathlib import Path
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.interfaces.file_downloader import FileDownloader
from src.domain.entities.transcript import Transcript
from src.infrastructure.services.media_converter import MediaConverter
from src.infrastructure.services.text_summarizer import TextSummarizer


class TranscribeAudioFileUseCase:
    def __init__(self, transcriber: AudioTranscriber, downloader: FileDownloader):
        self.transcriber = transcriber
        self.downloader = downloader
        self.converter = MediaConverter()

    def execute(self, file_name: str, sharepoint_link: str) -> Transcript:
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)

        file_path = downloads_dir / file_name
        self.downloader.download(sharepoint_link, str(file_path))

        # Si es un archivo MP4, convertirlo a MP3
        if file_path.suffix.lower() == '.mp4':
            audio_path = file_path.with_suffix('.mp3')
            self.converter.convert_video_to_audio(str(file_path), str(audio_path))
            file_path = audio_path

        transcript = self.transcriber.transcribe(str(file_path))

        # Resumir el texto si está disponible el API key de Anthropic
        if 'ANTHROPIC_API_KEY' in os.environ:
            try:
                summarizer = TextSummarizer()
                summary = summarizer.summarize(transcript.text)
                return Transcript(f"Transcripción original:\n\n{transcript.text}\n\nResumen:\n\n{summary}", transcript.source_file)
            except Exception as e:
                print(f"Error al resumir: {str(e)}")
                return transcript
        return transcript
