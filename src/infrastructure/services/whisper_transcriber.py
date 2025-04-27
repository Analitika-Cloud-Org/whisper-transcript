
import whisper
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_input) -> Transcript:
        # Usar modelo más pequeño
        model = whisper.load_model("tiny")

        # Si es BytesIO, guardar temporalmente
        if hasattr(file_input, 'read'):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp.write(file_input.getvalue())
                tmp_path = tmp.name
            result = model.transcribe(tmp_path)
            import os
            os.unlink(tmp_path)
        else:
            result = model.transcribe(file_input)

        return Transcript(result["text"], getattr(file_input, 'name', 'memory_file'))
