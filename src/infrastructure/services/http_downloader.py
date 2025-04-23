import requests
import msal
from src.domain.interfaces.file_downloader import FileDownloader

class HttpDownloader(FileDownloader):
    def __init__(self, client_id, client_secret, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def get_access_token(self):
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

        # Scope correcto para Microsoft Graph (que es donde configuraste los permisos)
        scopes = ["https://graph.microsoft.com/.default"]

        # Primero intentamos obtener el token de la caché
        result = app.acquire_token_silent(scopes, account=None)

        # Si no hay token en caché, lo solicitamos
        if not result:
            result = app.acquire_token_for_client(scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"No se pudo obtener el token: {result.get('error_description')}")

    def download(self, url: str, output_path: str) -> str:
        if 'sharepoint.com' in url:
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json;odata=verbose'  # Importante para SharePoint
            }

            # Si es una URL directa de SharePoint, la usamos directamente
            # Si necesitas convertir una ruta de SharePoint a una URL de descarga directa
            # tendrías que usar la API de Graph primero para obtener la URL de descarga

            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            # Para URLs no SharePoint, descarga directa sin token
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return output_path