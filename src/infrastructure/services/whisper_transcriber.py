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
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False) as temp_file:
            # Asegurarse de que el puntero esté al inicio
            file_input.seek(0)
            temp_file.write(file_input.getvalue())
            temp_file.flush()
            temp_path = temp_file.name

        try:
            # Transcribir inmediatamente después de cerrar el archivo
            result = model.transcribe(temp_path)
            source_name = getattr(file_input, 'name', 'memory_file')
            return Transcript(result["text"], source_name)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error al eliminar archivo temporal: {e}")
