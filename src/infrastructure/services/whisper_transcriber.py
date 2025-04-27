
import whisper
import tempfile
import os
from src.domain.interfaces.audio_transcriber import AudioTranscriber
from src.domain.entities.transcript import Transcript

class WhisperTranscriber(AudioTranscriber):
    def transcribe(self, file_input) -> Transcript:
        # Usar modelo más pequeño
        model = whisper.load_model("tiny")

        # Crear directorio temporal si no existe
        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_path = temp_file.name

        try:
            # Escribir datos al archivo temporal
            if hasattr(file_input, 'read'):
                temp_file.write(file_input.getvalue())
            else:
                with open(file_input, 'rb') as f:
                    temp_file.write(f.read())
            temp_file.flush()
            temp_file.close()

            # Transcribir
            result = model.transcribe(temp_path)
            return Transcript(result["text"], getattr(file_input, 'name', 'memory_file'))

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error al eliminar archivo temporal: {e}")
