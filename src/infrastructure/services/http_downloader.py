import requests
import msal
from src.domain.interfaces.file_downloader import FileDownloader
import sys
import os
from urllib.parse import urlparse

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

            # Analizar la URL para entender su estructura
            parsed_url = urlparse(url)
            sharepoint_domain = parsed_url.netloc  # analitikacloud.sharepoint.com

            # Determinar la estructura correcta
            path_segments = parsed_url.path.strip('/').split('/')

            print(f"Dominio: {sharepoint_domain}")
            print(f"Segmentos de ruta: {path_segments}")

            # El enfoque principal - obtener el drive por defecto del sitio
            # Primero obtener el sitio por su URL
            site_url = f"https://graph.microsoft.com/v1.0/sites/{sharepoint_domain}:/{path_segments[0]}"
            print(f"Consultando información del sitio: {site_url}")

            site_response = requests.get(site_url, headers=headers)
            if site_response.status_code != 200:
                print(f"Error al obtener información del sitio: {site_response.status_code}")
                print(f"Respuesta: {site_response.text[:500]}")
                raise Exception(f"No se pudo acceder al sitio: {site_response.status_code}")

            site_info = site_response.json()
            site_id = site_info.get('id')
            print(f"ID del sitio encontrado: {site_id}")

            # Obtener la drive por defecto del sitio
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            drives_response = requests.get(drives_url, headers=headers)
            if drives_response.status_code != 200:
                print(f"Error al obtener drives: {drives_response.status_code}")
                print(f"Respuesta: {drives_response.text[:500]}")
                raise Exception(f"No se pudieron obtener los drives: {drives_response.status_code}")

            drives = drives_response.json().get('value', [])
            if not drives:
                raise Exception("No se encontraron bibliotecas de documentos en el sitio")

            # Usar el primer drive (normalmente 'Documents' o 'Documentos')
            drive_id = drives[0].get('id')
            print(f"Usando drive ID: {drive_id}")

            # Construir la ruta del archivo dentro del drive
            # Excluyendo el primer segmento (nombre del sitio)
            file_relative_path = '/'.join(path_segments[1:])

            # Consultar el archivo directamente por su ruta
            file_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_relative_path}"
            print(f"Consultando archivo: {file_url}")

            file_response = requests.get(file_url, headers=headers)
            if file_response.status_code != 200:
                print(f"Error al obtener archivo: {file_response.status_code}")
                print(f"Respuesta: {file_response.text[:500]}")

                # Intentar estrategia alternativa - buscar por nombre
                items_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
                items_response = requests.get(items_url, headers=headers)

                if items_response.status_code == 200:
                    items = items_response.json().get('value', [])
                    file_name = path_segments[-1]
                    for item in items:
                        if item.get('name') == file_name:
                            file_info = item
                            break
                    else:
                        raise Exception(f"No se encontró el archivo: {file_name}")
                else:
                    raise Exception(f"No se pudo obtener el archivo: {file_response.status_code}")
            else:
                file_info = file_response.json()

            # Obtener la URL de descarga
            if "@microsoft.graph.downloadUrl" not in file_info:
                raise Exception("No se pudo obtener la URL de descarga")

            download_url = file_info["@microsoft.graph.downloadUrl"]
            print(f"URL de descarga obtenida: {download_url[:50]}...")

            # Descargar el archivo
            download_response = requests.get(download_url, stream=True)
            download_response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Archivo descargado exitosamente en: {output_path}")
            return output_path

        except Exception as e:
            raise Exception(f"Error al descargar el archivo: {str(e)}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python main.py <nombre_archivo_local> <url_sharepoint>")
        return

    local_file = sys.argv[1]
    sharepoint_url = sys.argv[2]

    # Configura tus credenciales aquí
    client_id = "TU_CLIENT_ID"
    client_secret = "TU_CLIENT_SECRET"
    tenant_id = "analitikacloud.onmicrosoft.com"

    try:
        downloader = HttpDownloader(client_id, client_secret, tenant_id)
        file_path = downloader.download(sharepoint_url, local_file)
        print(f"Archivo descargado en: {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()