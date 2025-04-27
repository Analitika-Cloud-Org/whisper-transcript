
from abc import ABC, abstractmethod
from src.domain.entities.transcript import Transcript

class AudioTranscriber(ABC):
    @abstractmethod
    def transcribe(self, file_path: str) -> Transcript:
        pass
