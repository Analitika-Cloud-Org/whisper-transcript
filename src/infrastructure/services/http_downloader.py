import requests
import msal
from src.domain.interfaces.file_downloader import FileDownloader

class HttpDownloader(FileDownloader):
    def __init__(self, token=None):
        self.token = token

    def download(self, url: str, output_path: str) -> str:
        if 'sharepoint.com' in url:
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return output_path