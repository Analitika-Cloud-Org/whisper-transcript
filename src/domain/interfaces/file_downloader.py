
from abc import ABC, abstractmethod
from typing import Tuple

class FileDownloader(ABC):
    @abstractmethod
    def download(self, url: str, output_path: str) -> Tuple[bytes, str]:
        pass
