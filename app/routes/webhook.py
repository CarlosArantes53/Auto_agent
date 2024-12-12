from flask import Blueprint, current_app, request, jsonify
from app.agentes.geral import process_message
from collections import defaultdict
import threading

webhook_bp = Blueprint('webhook', __name__)

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
            process_message(sender_id, message, user_message_queues, processing_locks)
    return jsonify({"status": "success"}), 200
