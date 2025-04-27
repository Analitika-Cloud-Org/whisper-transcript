
from abc import ABC, abstractmethod
from src.domain.entities.transcript import Transcript
import io

class AudioTranscriber(ABC):
    @abstractmethod
    def transcribe(self, file_input: io.BytesIO) -> Transcript:
        pass
