
import whisper
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_path: str) -> Transcript:
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        return Transcript(result["text"], file_path)
