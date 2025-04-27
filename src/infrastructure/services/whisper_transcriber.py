
import whisper
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_input) -> Transcript:
        model = whisper.load_model("medium")
        result = model.transcribe(file_input)
        return Transcript(result["text"], getattr(file_input, 'name', 'memory_file'))
