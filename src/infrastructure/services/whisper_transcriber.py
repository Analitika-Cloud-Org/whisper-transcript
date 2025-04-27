
import whisper
import tempfile
import os
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_input) -> Transcript:
        model = whisper.load_model("tiny")

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False, mode='wb') as tmp:
            if hasattr(file_input, 'read'):
                # Si es un objeto tipo BytesIO
                tmp.write(file_input.getvalue())
            else:
                # Si es una ruta de archivo
                with open(file_input, 'rb') as f:
                    tmp.write(f.read())

            tmp_path = tmp.name

        try:
            result = model.transcribe(tmp_path)
            return Transcript(result["text"], getattr(file_input, 'name', 'memory_file'))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
