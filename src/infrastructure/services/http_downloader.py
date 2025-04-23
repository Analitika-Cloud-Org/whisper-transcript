
import requests
from src.domain.interfaces.file_downloader import FileDownloader

class HttpDownloader(FileDownloader):
    def download(self, url: str, output_path: str) -> str:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path
