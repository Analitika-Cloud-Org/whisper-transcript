
from abc import ABC, abstractmethod

class FileDownloader(ABC):
    @abstractmethod
    def download(self, url: str, output_path: str) -> str:
        pass
