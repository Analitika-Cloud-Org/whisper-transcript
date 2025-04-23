import requests
import msal
from src.domain.interfaces.file_downloader import FileDownloader
import sys
import os
from urllib.parse import urlparse, unquote

class HttpDownloader(FileDownloader):
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def get_access_token(self):
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_silent(scopes, account=None)

        if not result:
            result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"No se pudo obtener el token: {result.get('error_description', 'Error desconocido')}")

    def download(self, url: str, output_path: str) -> str:
        try:
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            # Obtener el sitio y la ruta del archivo
            site_name = url.split('sharepoint.com/')[0].split('/')[-1]
            file_path = url.split('sharepoint.com/')[1]

            # Primero obtener el ID del sitio
            site_url = f"https://graph.microsoft.com/v1.0/sites/{site_name}.sharepoint.com:/sites/{site_name}"
            site_response = requests.get(site_url, headers=headers)
            site_response.raise_for_status()
            site_id = site_response.json()['id']

            # Ahora obtener el archivo usando el ID del sitio
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{file_path}"
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()

            file_info = response.json()
            if "@microsoft.graph.downloadUrl" not in file_info:
                raise Exception("No se pudo obtener la URL de descarga")

            download_url = file_info["@microsoft.graph.downloadUrl"]

            # Descargar el archivo
            download_response = requests.get(download_url, stream=True)
            download_response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_path

        except Exception as e:
            raise Exception(f"Error al descargar el archivo: {str(e)}")


def main():
    if len(sys.argv) != 3:
        print("Uso: python main.py <nombre_archivo_local> <url_sharepoint>")
        return

    local_file = sys.argv[1]
    sharepoint_url = sys.argv[2]

    # Reemplaza estos valores con tus credenciales
    client_id = "TU_CLIENT_ID"
    client_secret = "TU_CLIENT_SECRET"
    tenant_id = "analitikacloud.onmicrosoft.com"  # O el ID de tenant

    try:
        downloader = HttpDownloader(client_id, client_secret, tenant_id)
        downloader.download(sharepoint_url, local_file)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()