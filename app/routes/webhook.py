from flask import Blueprint, request, jsonify, current_app
from app.utils.media import download_media
from app.utils.json_manager import read_json, write_json
import google.generativeai as genai
from PIL import Image
import os
import threading
from collections import defaultdict
import time
import requests

webhook_bp = Blueprint('webhook', __name__)

# Configuração do Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = "gemini-1.5-flash"

# Filas para mensagens pendentes
user_message_queues = defaultdict(list)
processing_locks = defaultdict(threading.Lock)

@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == current_app.config['VERIFY_TOKEN']:
        return challenge
    return "Token inválido", 403

@webhook_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    data = request.json
    if 'messages' in data['entry'][0]['changes'][0]['value']:
        messages = data['entry'][0]['changes'][0]['value']['messages']
        for message in messages:
            sender_id = message.get("from")
            process_message(sender_id, message)
    return jsonify({"status": "success"}), 200

def process_message(sender_id, message):
    """Adiciona a mensagem à fila do usuário e inicia o temporizador."""
    user_message_queues[sender_id].append(message)

    # Inicia um temporizador para processar as mensagens após 3 segundos
    lock = processing_locks[sender_id]
    if not lock.locked():
        lock.acquire()
        threading.Timer(3, process_user_queue, args=(sender_id,)).start()
from app import create_app  # Certifique-se de importar a função para criar o app

def process_user_queue(sender_id):
    """Processa todas as mensagens acumuladas na fila de um usuário."""
    app = create_app()  # Cria o app para usar no contexto
    with app.app_context():
        try:
            messages = user_message_queues.pop(sender_id, [])
            lock = processing_locks[sender_id]

            if not messages:
                return

            prompts = []
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
                        prompts.append(f"Descreva esta imagem: {file_path}")
                    else:
                        prompts.append("Erro ao processar uma imagem enviada pelo cliente.")

            formatted_prompt = f"Você é um atendente de pet-shop e-commerce e deve responder em tom formal as seguintes solicitações do usuário:\n\n{'\n'.join(prompts)}"
            gemini_response = generate_response_from_gemini(formatted_prompt)

            # Envia a resposta para o cliente
            send_response_to_client(sender_id, gemini_response)

        finally:
            # Libera o lock para que novas mensagens possam ser processadas
            processing_locks[sender_id].release()

def generate_response_from_gemini(prompt):
    """Gera uma resposta do Google Gemini para o prompt acumulado."""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        current_app.logger.error(f"Erro na chamada da API do Gemini: {e}")
        return "Erro ao gerar resposta."

def send_response_to_client(recipient_id, message_text):
    """Envia uma mensagem de texto de resposta ao cliente."""
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message_text}
    }

    response = requests.post(current_app.config['WHATSAPP_API_URL'], headers=headers, json=data)
    if response.status_code != 200:
        current_app.logger.error(f"Erro ao enviar resposta ao cliente: {response.json()}")
