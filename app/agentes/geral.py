from threading import Timer
from app.utils.media import download_media
from PIL import Image
from pydub import AudioSegment
import json
from app.routes.gemini import send_response_to_client
from app.agentes.crew import crew

message_queues = {}

def convert_audio(file_path):
    try:
        if not file_path.endswith(".wav"):
            wav_path = file_path.replace(".ogg", ".wav")
            audio = AudioSegment.from_file(file_path)
            audio.export(wav_path, format="wav")
            file_path = wav_path
        return file_path
    except Exception as e:
        raise RuntimeError(f"Erro ao converter áudio: {e}")

class MessageProcessor:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.messages = []
        self.timer = None

    def add_message(self, message):
        self.messages.append(message)
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(3, self.process_messages)
        self.timer.start()

    def process_messages(self):
        inputs = {"pergunta": "", "preferencia_produto": "", "preferencia_servico": ""}

        for i, message in enumerate(self.messages):
            if message["type"] == "text":
                text = message.get("text", {}).get("body", "")
                inputs["pergunta"] += f" {text}".strip()
            elif message["type"] == "audio":
                media_id = message["audio"]["id"]
                mime_type = message["audio"]["mime_type"]
                file_path = download_media(media_id, mime_type)
                converted_path = convert_audio(file_path)
                inputs["pergunta"] += f" Áudio convertido: {converted_path}".strip()
            elif message["type"] == "image":
                inputs["pergunta"] += " Imagem recebida.".strip()

        resultado = crew.kickoff(inputs=inputs)

        response = "\n".join([task.output for task in resultado])

        send_response_to_client(self.sender_id, response)

        self.messages.clear()

message_processors = {}

def handle_message(sender_id, message):
    if sender_id not in message_processors:
        message_processors[sender_id] = MessageProcessor(sender_id)
    message_processors[sender_id].add_message(message)

def process_message(sender_id, message, user_message_queues, processing_locks):
    with processing_locks[sender_id]:
        user_message_queues[sender_id].append(message)
        handle_message(sender_id, message)
