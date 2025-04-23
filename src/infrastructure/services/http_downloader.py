import requests
import msal
import sys
import os
from urllib.parse import urlparse

def get_graph_token(client_id, client_secret, tenant_id):
    """Obtiene token para Microsoft Graph API"""
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret
    )

    scopes = ["https://graph.microsoft.com/.default"]
    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        print("Token de Microsoft Graph obtenido correctamente")
        return result["access_token"]
    else:
        raise Exception(f"No se pudo obtener el token: {result.get('error_description', 'Error desconocido')}")

def download_sharepoint_file(token, sharepoint_url, output_path):
    """Descarga un archivo de SharePoint usando Microsoft Graph API"""
    # Analizar la URL
    parsed_url = urlparse(sharepoint_url)
    hostname = parsed_url.netloc
    path_segments = parsed_url.path.strip('/').split('/')

    # Extraer nombre del sitio (primer segmento) y nombre del archivo (último segmento)
    site_name = path_segments[0]
    file_name = path_segments[-1]

    print(f"URL de SharePoint: {sharepoint_url}")
    print(f"Host: {hostname}")
    print(f"Sitio: {site_name}")
    print(f"Nombre del archivo: {file_name}")

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    # ESTRATEGIA 1: Obtener el sitio primero
    site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site_name}"
    print(f"Obteniendo información del sitio: {site_url}")

    site_response = requests.get(site_url, headers=headers)

    if site_response.status_code != 200:
        print(f"Error al obtener información del sitio: {site_response.status_code}")
        print(f"Respuesta: {site_response.text}")

        # Intentar obtener por dominio sin '/sites/'
        site_url_alt = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/{site_name}"
        print(f"Intentando alternativa: {site_url_alt}")
        site_response = requests.get(site_url_alt, headers=headers)

        if site_response.status_code != 200:
            print(f"Error en alternativa: {site_response.status_code}")
            raise Exception(f"No se pudo obtener información del sitio: {site_response.status_code}")

    site_info = site_response.json()
    site_id = site_info.get('id')
    print(f"ID del sitio: {site_id}")

    # ESTRATEGIA 2: Listar todas las drives (bibliotecas) del sitio
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    print(f"Obteniendo drives: {drives_url}")

    drives_response = requests.get(drives_url, headers=headers)
    if drives_response.status_code != 200:
        print(f"Error al obtener drives: {drives_response.status_code}")
        print(f"Respuesta: {drives_response.text}")
        raise Exception(f"No se pudieron obtener los drives del sitio: {drives_response.status_code}")

    drives = drives_response.json().get('value', [])
    if not drives:
        raise Exception("No se encontraron bibliotecas de documentos en el sitio")

    # Listar todos los drives
    print("Bibliotecas disponibles:")
    for i, drive in enumerate(drives):
        print(f"  {i+1}. {drive.get('name')} (ID: {drive.get('id')})")

    # Usar el primer drive por defecto
    drive_id = drives[0].get('id')
    drive_name = drives[0].get('name')
    print(f"Usando biblioteca: {drive_name} (ID: {drive_id})")

    # ESTRATEGIA 3: Buscar el archivo por nombre en la raíz de la biblioteca
    search_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/search(q='{file_name}')"
    print(f"Buscando archivo '{file_name}': {search_url}")

    search_response = requests.get(search_url, headers=headers)
    if search_response.status_code != 200:
        print(f"Error en la búsqueda: {search_response.status_code}")
        print(f"Respuesta: {search_response.text}")
        raise Exception(f"Error al buscar el archivo: {search_response.status_code}")

    search_results = search_response.json().get('value', [])
    if not search_results:
        # Si no hay resultados, intentar listar todos los archivos
        print("No se encontró el archivo por búsqueda, listando todos los archivos...")
        list_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        list_response = requests.get(list_url, headers=headers)

        if list_response.status_code == 200:
            files = list_response.json().get('value', [])
            print(f"Archivos en la raíz de {drive_name}:")
            for file in files:
                print(f"  - {file.get('name')} ({file.get('id')})")

            # Buscar el archivo en la lista
            matching_files = [f for f in files if f.get('name').lower() == file_name.lower()]
            if matching_files:
                file_info = matching_files[0]
                print(f"Archivo encontrado por nombre: {file_info.get('name')}")
            else:
                raise Exception(f"No se encontró el archivo '{file_name}' en la biblioteca")
        else:
            raise Exception(f"No se pudo listar los archivos: {list_response.status_code}")
    else:
        # Usar el primer resultado de la búsqueda
        file_info = search_results[0]
        print(f"Archivo encontrado por búsqueda: {file_info.get('name')}")

    # Obtener la URL de descarga del archivo encontrado
    file_id = file_info.get('id')
    download_info_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{file_id}"
    download_info_response = requests.get(download_info_url, headers=headers)

    if download_info_response.status_code != 200:
        print(f"Error al obtener información de descarga: {download_info_response.status_code}")
        print(f"Respuesta: {download_info_response.text}")
        raise Exception(f"No se pudo obtener información para descargar: {download_info_response.status_code}")

    download_info = download_info_response.json()
    if "@microsoft.graph.downloadUrl" not in download_info:
        raise Exception("No se encontró la URL de descarga en la respuesta")

    download_url = download_info["@microsoft.graph.downloadUrl"]
    print(f"URL de descarga obtenida: {download_url[:50]}...")

    # Descargar el archivo usando la URL obtenida
    print(f"Descargando archivo a {output_path}...")
    download_response = requests.get(download_url, stream=True)
    download_response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"¡Archivo descargado exitosamente en: {output_path}!")
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
        # Obtener token para Microsoft Graph
        token = get_graph_token(client_id, client_secret, tenant_id)

        # Descargar el archivo
        download_sharepoint_file(token, sharepoint_url, local_file)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()