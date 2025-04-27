
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

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_input.getvalue())
            temp_file.flush()

            # Transcribir
            result = model.transcribe(temp_path)

            # Obtener nombre del archivo de la fuente
            if isinstance(file_input, (io.BytesIO, io.BufferedRandom)):
                source_name = getattr(file_input, 'name', 'memory_file')
            else:
                source_name = os.path.basename(file_input)

            return Transcript(result["text"], source_name)

        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error al eliminar archivo temporal: {e}")
