import os
import requests

def download_media(media_id, mime_type):
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    media_url = f"https://graph.facebook.com/v16.0/{media_id}"

    # Criação do diretório caso não exista
    media_dir = "media_files"
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)

    response = requests.get(media_url, headers=headers)
    if response.status_code == 200:
        file_url = response.json().get("url")
        file_response = requests.get(file_url, headers=headers, stream=True)

        if file_response.status_code == 200:
            # Obtenha a extensão correta do arquivo
            extension = mime_type.split("/")[-1]
            file_path = os.path.join(media_dir, f"{media_id}.{extension}")

            # Salve o arquivo
            with open(file_path, "wb") as file:
                for chunk in file_response.iter_content(chunk_size=1024):
                    file.write(chunk)
            return file_path

    return None
