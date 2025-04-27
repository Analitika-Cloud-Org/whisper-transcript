import sys
import os
from dotenv import load_dotenv
from src.infrastructure.services.whisper_transcriber import WhisperTranscriber
from src.infrastructure.services.http_downloader import HttpDownloader

load_dotenv()
from src.application.use_cases.transcribe_audio_file import TranscribeAudioFileUseCase

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <filename> <sharepoint_link>")
        return

    filename = sys.argv[1]
    sharepoint_link = sys.argv[2]

    # Initialize dependencies
    transcriber = WhisperTranscriber()
    client_id = os.environ['SHAREPOINT_CLIENT_ID']
    client_secret = os.environ['SHAREPOINT_CLIENT_SECRET']
    tenant_id = os.environ['SHAREPOINT_TENANT_ID']

    if not all([client_id, client_secret, tenant_id]):
        print("Error: Asegúrate de configurar todas las variables de entorno en el archivo .env")
        return

    downloader = HttpDownloader(client_id, client_secret, tenant_id)
    use_case = TranscribeAudioFileUseCase(transcriber, downloader)

    # Execute use case
    try:
        transcript = use_case.execute(filename, sharepoint_link)

        # Save transcript
        output_file = f"{filename}_transcript.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript.text)

        print(f"Transcription saved to: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()