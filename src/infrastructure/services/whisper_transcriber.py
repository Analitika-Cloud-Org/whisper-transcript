
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

        # Crear directorio temporal si no existe
        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_path = temp_file.name

        try:
            # Manejar entrada como BytesIO o ruta de archivo
            if isinstance(file_input, (io.BytesIO, io.BufferedRandom)):
                temp_file.write(file_input.getvalue())
            elif isinstance(file_input, str):
                if not os.path.exists(file_input):
                    raise FileNotFoundError(f"El archivo {file_input} no existe")
                with open(file_input, 'rb') as f:
                    temp_file.write(f.read())
            else:
                raise ValueError("Input debe ser BytesIO o ruta de archivo")

            temp_file.flush()
            temp_file.close()

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
