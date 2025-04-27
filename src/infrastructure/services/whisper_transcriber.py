
import whisper
import tempfile
import os
import io
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_input) -> Transcript:
        print(f"Tipo de input recibido en transcribe: {type(file_input)}, valor: {file_input}")
        model = whisper.load_model("tiny")

        if not isinstance(file_input, io.BytesIO):
            raise ValueError("El input debe ser BytesIO")

        # Usar un contexto temporal más corto y en memoria RAM
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=True) as temp_file:
            # Escribir datos directamente
            file_input.seek(0)
            temp_file.write(file_input.getvalue())
            temp_file.flush()

            # Transcribir inmediatamente
            result = model.transcribe(temp_file.name)

            # Obtener nombre del archivo de la fuente
            source_name = getattr(file_input, 'name', 'memory_file')

            return Transcript(result["text"], source_name)
