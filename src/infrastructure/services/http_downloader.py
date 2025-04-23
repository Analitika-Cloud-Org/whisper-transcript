import requests
import msal
import sys
import os
from urllib.parse import urlparse, unquote

def get_graph_token(client_id, client_secret, tenant_id):
    """
    Obtiene un token para acceder a Microsoft Graph API
    """
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret
    )

    # Microsoft Graph requiere este scope específico
    scopes = ["https://graph.microsoft.com/.default"]

    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        print("Token de Microsoft Graph obtenido correctamente")
        return result["access_token"]
    else:
        error_msg = result.get('error_description', 'Error desconocido')
        raise Exception(f"No se pudo obtener el token de Graph: {error_msg}")

def get_download_url_from_sharepoint_path(token, sharepoint_url):
    """
    Convierte una URL de SharePoint en una URL de descarga directa usando Microsoft Graph
    """
    # Analizar la URL de SharePoint
    parsed_url = urlparse(sharepoint_url)
    host = parsed_url.netloc  # Ejemplo: 'analitikacloud.sharepoint.com'

    # Extraer el nombre del sitio y la ruta del archivo
    path_parts = parsed_url.path.strip('/').split('/')

    # Generalmente el primer segmento después del dominio es el nombre del sitio/colección
    # y el resto es la ruta al archivo
    if len(path_parts) < 2:
        raise ValueError(f"URL de SharePoint no válida o incompleta: {sharepoint_url}")

    site_name = path_parts[0]
    file_path = '/'.join(path_parts[1:])

    print(f"Host: {host}")
    print(f"Sitio: {site_name}")
    print(f"Ruta del archivo: {file_path}")

    # Primera estrategia: intentar obtener directamente a través de /sites/
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    # 1. Intentar obtener el recurso a través de /sites/{site}/drive/root:/path/to/file
    encoded_file_path = '/'.join(path_parts[1:])
    graph_url = f"https://graph.microsoft.com/v1.0/sites/{host}:/{site_name}:/drive/root:/{encoded_file_path}"

    print(f"Intentando acceder al archivo vía: {graph_url}")
    response = requests.get(graph_url, headers=headers)

    # Si falla, intentemos otra estrategia usando site ID
    if response.status_code != 200:
        print(f"Primer intento falló con código {response.status_code}")
        print(f"Intentando estrategia alternativa...")

        # 2. Obtener el ID del sitio primero
        site_url = f"https://graph.microsoft.com/v1.0/sites/{host}:/sites/{site_name}"
        site_response = requests.get(site_url, headers=headers)

        if site_response.status_code != 200:
            print(f"No se pudo obtener información del sitio: {site_response.status_code}")
            print(f"Respuesta: {site_response.text[:500]}")
            raise Exception(f"No se pudo acceder al sitio de SharePoint: {site_response.status_code}")

        site_info = site_response.json()
        site_id = site_info.get('id')

        # 3. Obtener información del archivo usando el ID del sitio
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{encoded_file_path}"
        print(f"Intentando con ID de sitio: {graph_url}")
        response = requests.get(graph_url, headers=headers)

    if response.status_code == 200:
        file_info = response.json()
        # Verificar si tenemos la URL de descarga
        if "@microsoft.graph.downloadUrl" in file_info:
            download_url = file_info["@microsoft.graph.downloadUrl"]
            print(f"URL de descarga obtenida correctamente")
            return download_url
        else:
            print("No se encontró la URL de descarga en la respuesta")
            print(f"Respuesta: {file_info}")
            raise Exception("No se pudo obtener la URL de descarga del archivo")
    else:
        print(f"Error al acceder al archivo: {response.status_code}")
        print(f"Respuesta: {response.text[:500]}")

        # Intentar una última estrategia como respaldo (usando la biblioteca 'Documents')
        try:
            docs_url = f"https://graph.microsoft.com/v1.0/sites/{host}:/sites/{site_name}:/drives"
            drives_response = requests.get(docs_url, headers=headers)

            if drives_response.status_code == 200:
                drives = drives_response.json().get('value', [])
                if drives:
                    drive_id = drives[0].get('id')
                    # Intentar obtener el archivo por la biblioteca por defecto
                    file_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_file_path}"
                    file_response = requests.get(file_url, headers=headers)

                    if file_response.status_code == 200:
                        file_info = file_response.json()
                        if "@microsoft.graph.downloadUrl" in file_info:
                            return file_info["@microsoft.graph.downloadUrl"]

            raise Exception(f"No se pudo acceder al archivo después de múltiples intentos")
        except Exception as e:
            print(f"Error en estrategia de respaldo: {str(e)}")
            raise Exception(f"No se pudo acceder al archivo: {response.status_code} - {response.text[:500]}")

def download_file(url, output_path):
    """
    Descarga un archivo desde una URL directa
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Archivo descargado exitosamente en: {output_path}")
    return output_path

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
        # 1. Obtener token para Microsoft Graph
        token = get_graph_token(client_id, client_secret, tenant_id)

        # 2. Usar Microsoft Graph para obtener la URL de descarga directa
        download_url = get_download_url_from_sharepoint_path(token, sharepoint_url)

        # 3. Descargar el archivo usando la URL directa (no requiere autenticación)
        download_file(download_url, local_file)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()