from app.utils.media import download_media
from app.routes.gemini import generate_response_from_gemini, send_response_to_client
from app import create_app
import threading
from PIL import Image

def process_message(sender_id, message, user_message_queues, processing_locks):
    """Adiciona mensagem à fila e inicia temporizador."""
    user_message_queues[sender_id].append(message)

    lock = processing_locks[sender_id]
    if not lock.locked():
        lock.acquire()
        threading.Timer(3, process_user_queue, args=(sender_id, user_message_queues, processing_locks)).start()

def process_user_queue(sender_id, user_message_queues, processing_locks):
    """Processa mensagens acumuladas de um usuário."""
    app = create_app()
    with app.app_context():
        try:
            messages = user_message_queues.pop(sender_id, [])
            lock = processing_locks[sender_id]

            if not messages:
                return

            prompts = []
            image_objects = []
            for message in messages:
                message_type = message.get("type")
                if message_type == "text":
                    user_prompt = message.get("text", {}).get("body")
                    prompts.append(user_prompt)
                elif message_type == "image":
                    media_id = message["image"]["id"]
                    mime_type = message["image"]["mime_type"]
                    file_path = download_media(media_id, mime_type)
                    if file_path:
                        try:
                            img = Image.open(file_path)
                            image_objects.append(img)
                            prompts.append("Veja a imagem fornecida.")
                        except Exception as e:
                            prompts.append(f"Erro ao processar uma imagem enviada pelo cliente: {str(e)}")
                    else:
                        prompts.append("Erro ao baixar uma imagem enviada pelo cliente.")

            # Cria o prompt formatado
            formatted_prompt = f"Você é um atendente de pet-shop e-commerce e deve responder em tom formal às seguintes solicitações do usuário:\n\n{'\n'.join(prompts)}"
            
            # Gera a resposta do Gemini, incluindo imagens
            gemini_response = generate_response_from_gemini(formatted_prompt, image_objects)

            # Envia a resposta ao cliente
            send_response_to_client(sender_id, gemini_response)

        finally:
            processing_locks[sender_id].release()
