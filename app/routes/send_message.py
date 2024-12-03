from flask import Blueprint, request, jsonify, current_app
import requests

send_message_bp = Blueprint('send_message', __name__)

@send_message_bp.route('/send_message', methods=['POST'])
def send_message():
    payload = request.json
    recipient_number = payload.get("to")
    message_text = payload.get("message")

    if not recipient_number or not message_text:
        return jsonify({"error": "O número do destinatário e a mensagem são obrigatórios"}), 400

    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message_text}
    }

    response = requests.post(current_app.config['WHATSAPP_API_URL'], headers=headers, json=data)
    return jsonify(response.json()), response.status_code
