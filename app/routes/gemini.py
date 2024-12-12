from flask import current_app
import google.generativeai as genai
import requests
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = "gemini-1.5-flash"

def generate_response_from_gemini(prompt, images=None):
    try:
        model = genai.GenerativeModel(model_name)
        inputs = [prompt]
        if images:
            inputs.extend(images)
        response = model.generate_content(inputs)
        return response.text
    except Exception as e:
        current_app.logger.error(f"Erro na chamada da API do Gemini: {e}")
        return "Erro ao gerar resposta."


def send_response_to_client(recipient_id, message_text):
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
