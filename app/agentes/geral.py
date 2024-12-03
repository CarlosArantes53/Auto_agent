from app.utils.media import download_media
from app.routes.gemini import generate_response_from_gemini, send_response_to_client
from app import create_app
import threading
from PIL import Image

def process_message(sender_id, message, user_message_queues, processing_locks):
    user_message_queues[sender_id].append(message)

    lock = processing_locks[sender_id]
    if not lock.locked():
        lock.acquire()
        threading.Timer(3, process_user_queue, args=(sender_id, user_message_queues, processing_locks)).start()

chat_histories = {}

def process_user_queue(sender_id, user_message_queues, processing_locks):
    app = create_app()
    with app.app_context():
        try:
            messages = user_message_queues.pop(sender_id, [])
            lock = processing_locks[sender_id]

            if not messages:
                return

            if sender_id not in chat_histories:
                chat_histories[sender_id] = []

            prompts = []
            image_objects = []

            for message in messages:
                message_type = message.get("type")
                if message_type == "text":
                    user_prompt = message.get("text", {}).get("body")
                    prompts.append(user_prompt)
                    chat_histories[sender_id].append({"role": "user", "content": user_prompt})
                elif message_type == "image":
                    media_id = message["image"]["id"]
                    mime_type = message["image"]["mime_type"]
                    file_path = download_media(media_id, mime_type)
                    if file_path:
                        try:
                            img = Image.open(file_path)
                            image_objects.append(img)
                            prompts.append("Veja a imagem fornecida.")
                            chat_histories[sender_id].append({"role": "user", "content": "Imagem fornecida."})
                        except Exception as e:
                            prompts.append(f"Erro ao processar uma imagem enviada pelo cliente: {str(e)}")
                            chat_histories[sender_id].append({"role": "user", "content": "Erro ao processar imagem."})
                    else:
                        prompts.append("Erro ao baixar uma imagem enviada pelo cliente.")
                        chat_histories[sender_id].append({"role": "user", "content": "Erro ao baixar imagem."})

            history_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_histories[sender_id]])
            prompt_to_llm = f"""{history_prompt}
Você é um atendente de um pet-shop e-commerce especializado em oferecer um atendimento atencioso e personalizado. Sua tarefa é responder às solicitações do usuário de maneira formal, mas com um tom acolhedor e próximo.

Histórico de interações:
{'\n'.join(prompts)}

Agora, com base na mensagem mais recente do usuário:
- Avalie se ele deseja encerrar o chat ou continuar a conversa. Se desejar encerrar, responda educadamente e confirme o término da interação, usando palavras gentis como "Foi um prazer ajudar você! 😊". 
- Se ele desejar continuar, siga normalmente com o atendimento, oferecendo respostas úteis e completas.
- Caso a mensagem seja ambígua ou você não tenha certeza, pergunte ao usuário de forma educada, como: "Não entendi muito bem. Poderia explicar melhor para que eu possa ajudar da melhor forma? 😊".

Orientações adicionais:
- Nunca encerre o chat se o usuário apenas cumprimentar, perguntar algo ou solicitar informações. Exemplo de mensagens que NÃO encerram: "Oi", "Olá", "Como funciona?", "Quero informações".
- Exemplo de mensagens que indicam o encerramento do chat: "Finalizar", "Obrigado, não preciso de mais nada", "Encerrar chat".
- Sempre inicie com uma saudação amigável no começo do chat, como "Olá! Como posso ajudar hoje? 😊". Em conversas continuadas, não repita a saudação inicial e não continue saudando o usuário.

Lembre-se:
- Seja sempre cordial, demonstre empatia e use emojis com moderação para tornar a interação mais leve e humana.
- Evite parecer robótico ou distante; responda como faria uma pessoa real, atenta e gentil.
"""

            gemini_response = generate_response_from_gemini(prompt_to_llm, image_objects)

            chat_histories[sender_id].append({"role": "assistant", "content": gemini_response})

            send_response_to_client(sender_id, gemini_response)

        finally:
            processing_locks[sender_id].release()