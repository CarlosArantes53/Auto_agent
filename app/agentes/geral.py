from crew import Crew
from crew.tasks import MediaProcessingTask, TextProcessingTask
from app.utils.media import download_media
from PIL import Image
from pydub import AudioSegment
import whisper
import pandas as pd
import json
import os

# Configuração do modelo Whisper
whisper_model = whisper.load_model("base")

# Carregamento de dados globais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, "produtos.csv")
SERVICES_FILE = os.path.join(BASE_DIR, "servicos.csv")
GENERAL_FILE = os.path.join(BASE_DIR, "geral.txt")

dados_produtos = pd.read_csv(PRODUCTS_FILE, sep=";")
dados_servicos = pd.read_csv(SERVICES_FILE, sep=";")
with open(GENERAL_FILE, "r", encoding="utf-8") as f:
    dados_gerais = f.read()

# Configuração do Crew
crew = Crew()

# Funções auxiliares
def gerar_e_salvar_json(sender_id, tipo_atendimento, valor=None, data=None):
    json_data = {
        "sender_id": sender_id,
        "tipo_atendimento": tipo_atendimento,
        "valor": valor,
        "data": data
    }
    file_name = f"{tipo_atendimento}_atendimento_{sender_id}.json"
    file_path = os.path.join(BASE_DIR, file_name)
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar JSON: {e}")

def convert_to_wav(input_path, output_path):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        raise RuntimeError(f"Erro ao converter áudio: {e}")

def transcribe_audio(file_path):
    try:
        if not file_path.endswith(".wav"):
            wav_path = file_path.replace(".ogg", ".wav")
            file_path = convert_to_wav(file_path, wav_path)
        result = whisper_model.transcribe(file_path)
        return result["text"]
    except Exception as e:
        raise RuntimeError(f"Erro ao transcrever áudio: {e}")

# Processamento com Crew AI
@crew.task
class ProcessUserMessageTask(MediaProcessingTask):
    def run(self, sender_id, message):
        try:
            if message["type"] == "text":
                return {"content": message.get("text", {}).get("body")}
            elif message["type"] == "image":
                media_id = message["image"]["id"]
                mime_type = message["image"]["mime_type"]
                file_path = download_media(media_id, mime_type)
                Image.open(file_path)  # Verifica se a imagem é válida
                return {"content": "Imagem fornecida."}
            elif message["type"] == "audio":
                media_id = message["audio"]["id"]
                mime_type = message["audio"]["mime_type"]
                file_path = download_media(media_id, mime_type)
                transcription = transcribe_audio(file_path)
                return {"content": transcription}
        except Exception as e:
            return {"error": str(e)}

@crew.task
class GenerateResponseTask(TextProcessingTask):
    def run(self, sender_id, history_prompt, latest_prompts):
        context_prompt = f"""
Você é um atendente de um pet-shop e-commerce. Seu objetivo é responder de maneira clara e eficiente.
Antes de confirmar uma compra, pergunte o nome completo da pessoa e, no caso de ser um serviço, solicite data de agendamento.
Se o usuário não for claro sobre o tipo de ração ou animal, pergunte para ajudar na compra ou agendamento.
Finalize respostas com:
- "Pedido confirmado" para compras.
- "Serviço agendado" para serviços.
- "Atendimento encerrado" se o atendimento terminar.

Produtos disponíveis:
{dados_produtos.to_string(index=False)}
Serviços disponíveis:
{dados_servicos.to_string(index=False)}
Informações gerais:
{dados_gerais}

Histórico de interações:
{history_prompt}

Mensagem mais recente:
{latest_prompts}
"""
        # Gerar resposta usando um método preexistente
        response = generate_response_from_gemini(context_prompt)
        return response

# Fluxo principal
def process_message(sender_id, message):
    user_history = []

    # Adiciona mensagem ao histórico
    if "messages" not in user_history:
        user_history.append(message)

    # Processa mensagem do usuário
    process_result = ProcessUserMessageTask().execute(sender_id, message)

    # Gera resposta
    response_task = GenerateResponseTask()
    history_prompt = "\n".join([f"{msg['content']}" for msg in user_history])
    gemini_response = response_task.execute(sender_id, history_prompt, process_result.get("content"))

    # Executa lógica de resposta
    if "pedido confirmado" in gemini_response.lower():
        gerar_e_salvar_json(sender_id, "produto")
    elif "serviço agendado" in gemini_response.lower():
        gerar_e_salvar_json(sender_id, "serviço")
    elif "atendimento encerrado" in gemini_response.lower():
        gerar_e_salvar_json(sender_id, "geral")
        user_history.clear()
    else:
        user_history.append({"role": "assistant", "content": gemini_response})
