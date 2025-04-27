import os
import io 
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
        if not file_name.lower().endswith('.mp3'):
            file_name = f"{file_name}.mp3"

        # Download file to memory
        file_content, file_path = self.downloader.download(sharepoint_link, file_name)

        # Create BytesIO object
        file_in_memory = io.BytesIO(file_content)
        file_in_memory.name = file_name  # Whisper needs the filename

        # Transcribe directly from memory
        transcript = self.transcriber.transcribe(file_in_memory)

        # Save transcript
        transcript_file = f"{file_name[:-4]}_transcript.txt"
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript.text)
        print(f"Transcripción guardada en: {transcript_file}")

        # Save summary if available
        if 'ANTHROPIC_API_KEY' in os.environ:
            try:
                summarizer = TextSummarizer()
                summary = summarizer.summarize(transcript.text)
                summary_file = f"{file_name[:-4]}_summary.txt"
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"Resumen guardado en: {summary_file}")
            except Exception as e:
                print(f"Error al guardar el resumen: {str(e)}")

        return transcript