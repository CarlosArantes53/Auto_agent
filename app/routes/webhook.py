from flask import Blueprint, request, jsonify, current_app
from app.utils.media import download_media
from app.utils.json_manager import read_json, write_json
import google.generativeai as genai
from PIL import Image
import os
import requests

webhook_bp = Blueprint('webhook', __name__)

# Configuração do Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = "gemini-1.5-flash"

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
        existing_data = read_json("messages.json")

        for message in messages:
            message_type = message.get("type")
            sender_id = message.get("from")
            formatted_message = {
                "from": sender_id,
                "id": message.get("id"),
                "timestamp": message.get("timestamp"),
                "type": message_type
            }

            # Gera uma resposta do Google Gemini com base no tipo de mensagem
            if message_type == "text":
                user_prompt = message.get("text", {}).get("body")
                gemini_response = generate_response_from_gemini(user_prompt)
                formatted_message["text"] = user_prompt
            elif message_type in ["image"]:
                media_id = message[message_type]["id"]
                mime_type = message[message_type]["mime_type"]
                file_path = download_media(media_id, mime_type)
                if file_path:
                    gemini_response = generate_image_description(file_path)
                else:
                    gemini_response = "Erro ao processar a imagem."
                formatted_message[message_type] = {"media_id": media_id, "file_path": file_path}
            else:
                gemini_response = "Tipo de mensagem não suportado."

            # Adiciona a mensagem processada ao arquivo JSON
            existing_data.append(formatted_message)

            # Envia a resposta gerada ao cliente
            send_response_to_client(sender_id, gemini_response)

        # Salva o JSON atualizado
        write_json("messages.json", existing_data)

    return jsonify({"status": "success"}), 200

def generate_response_from_gemini(prompt):
    """Gera resposta do Google Gemini para mensagens de texto."""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        current_app.logger.error(f"Erro na chamada da API do Gemini: {e}")
        return "Erro ao gerar resposta."

def generate_image_description(image_path):
    """Gera descrição do Google Gemini para mensagens de imagem."""
    try:
        model = genai.GenerativeModel(model_name)
        with Image.open(image_path) as img:
            response = model.generate_content(["O que você vê nessa imagem?", img])
        return response.text
    except Exception as e:
        current_app.logger.error(f"Erro na chamada da API do Gemini: {e}")
        return "Erro ao descrever a imagem."

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
