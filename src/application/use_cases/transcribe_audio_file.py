import os
from pathlib import Path
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.interfaces.file_downloader import FileDownloader
from src.domain.entities.transcript import Transcript
from src.infrastructure.services.media_converter import MediaConverter
from src.infrastructure.services.text_summarizer import TextSummarizer


class TranscribeAudioFileUseCase:

    def __init__(self, transcriber: AudioTranscriber,
                 downloader: FileDownloader):
        self.transcriber = transcriber
        self.downloader = downloader
        self.converter = MediaConverter()

    def execute(self, file_name: str, sharepoint_link: str) -> Transcript:
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        print(f"Created downloads directory at: {downloads_dir.absolute()}")

        # Asegurarse de que el nombre del archivo incluya la extensión
        if not file_name.lower().endswith('.mp3'):
            file_name = f"{file_name}.mp3"

        file_path = downloads_dir / file_name.replace('[', '_').replace(']', '_')
        print(f"Full file path: {file_path.absolute()}")
        print(f"Attempting to download file to: {file_path.absolute()}")

        downloaded_path = self.downloader.download(sharepoint_link, str(file_path))
        print(f"File downloaded to: {downloaded_path}")

        # Verificar que el archivo existe usando la ruta completa
        downloaded_file = Path(downloaded_path)

        #Added file verification
        total_size = downloaded_file.stat().st_size
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            if os.path.exists(downloaded_path):
                current_size = os.path.getsize(downloaded_path)
                if current_size >= total_size:
                    break
            time.sleep(1)
            attempts += 1
            print(f"Waiting for file to be completely written... Size: {current_size}/{total_size} bytes")

        if not downloaded_file.exists():
            raise FileNotFoundError(f"Downloaded file not found at: {downloaded_path}")

        if os.path.getsize(downloaded_path) < total_size:
            raise Exception(f"File was not completely written. Expected: {total_size} bytes, Got: {os.path.getsize(downloaded_path)} bytes")

        print(f"File size verification complete: {downloaded_file.stat().st_size} bytes")


        print(f"File size: {downloaded_file.stat().st_size} bytes")

        # Si es un archivo MP4, convertirlo a MP3
        if file_path.suffix.lower() == '.mp4':
            audio_path = file_path.with_suffix('.mp3')
            self.converter.convert_video_to_audio(str(file_path),
                                                  str(audio_path))
            file_path = audio_path

        # Usar la ruta completa para la transcripción
        transcript = self.transcriber.transcribe(str(downloaded_file.absolute()))

        # Save transcript
        transcript_file = f"{file_name[:-4]}_transcript.txt"  #removed unnecessary filename variable
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript.text)
        print(f"Transcripción guardada en: {transcript_file}")

        # Save summary if available
        if 'ANTHROPIC_API_KEY' in os.environ:
            try:
                summarizer = TextSummarizer()
                summary = summarizer.summarize(transcript.text)
                summary_file = f"{file_name[:-4]}_summary.txt"  #removed unnecessary filename variable
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"Resumen guardado en: {summary_file}")
            except Exception as e:
                print(f"Error al guardar el resumen: {str(e)}")
        return transcript