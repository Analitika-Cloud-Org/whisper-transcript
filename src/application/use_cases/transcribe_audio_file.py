
from pathlib import Path
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.interfaces.file_downloader import FileDownloader
from src.domain.entities.transcript import Transcript

class TranscribeAudioFileUseCase:
    def __init__(self, transcriber: AudioTranscriber, downloader: FileDownloader):
        self.transcriber = transcriber
        self.downloader = downloader

    def execute(self, file_name: str, sharepoint_link: str) -> Transcript:
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)

        audio_path = downloads_dir / file_name
        self.downloader.download(sharepoint_link, str(audio_path))

        return self.transcriber.transcribe(str(audio_path))
