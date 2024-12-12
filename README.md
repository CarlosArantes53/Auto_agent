# Integração com WhatsApp e Agentes de IA - PetShop Amigo Fiel

Este projeto implementa um sistema de atendimento automatizado utilizando a API do WhatsApp, agentes inteligentes baseados em LLM (Modelos de Linguagem de Grande Escala) e ferramentas auxiliares para um fluxo eficiente e responsivo.

## Funcionalidades

- **Integração com WhatsApp**: A aplicação utiliza a API do WhatsApp para envio e recebimento de mensagens. Um webhook local, configurado com o auxílio do `ngrok`, é responsável por processar as mensagens recebidas e enviar respostas.
- **Processamento de Mensagens**: As mensagens dos usuários são organizadas em filas específicas por remetente, com um tempo de espera de 3 segundos entre as mensagens para garantir um fluxo natural.
- **Agentes Inteligentes (Crew)**:
  - **Agente Central**: Fornece informações gerais sobre o PetShop, incluindo horários, equipe e promoções.
  - **Especialista em Produtos**: Recomenda produtos adequados com base nas preferências do usuário.
  - **Especialista em Serviços**: Sugere serviços baseados nas necessidades apresentadas pelo cliente.
- **Agente para geração de prompt**:
  - **Geração e organização do prompt**: Recebe as mensagens, áudios ou fotos do usuário, passa para o gemini sumarizar e retornar para o módulo **crew.py** o prompt gerado.
- **Geração de Respostas**: As respostas aos usuários são geradas por um modelo de IA, integrado ao sistema via API, que utiliza prompts customizados com base nas interações recebidas.

## Estrutura do Fluxo

1. **Recebimento de Mensagens**: As mensagens enviadas pelos usuários são capturadas pelo webhook, que está ativo localmente com suporte do `ngrok`.
2. **Processamento Inicial**: Cada mensagem é atribuída a um processador dedicado ao remetente, garantindo isolamento e contexto durante o processamento.
3. **Espera de 3 Segundos**: Um temporizador inicia após o recebimento de cada mensagem, permitindo que mensagens adicionais sejam agrupadas e processadas como uma única interação.
4. **Interação com Agentes**:
   - A mensagem do usuário é analisada e os dados relevantes são extraídos.
   - Os agentes especializados (Central, Produtos, Serviços) recebem as consultas em seus respectivos domínios.
   - As respostas são geradas utilizando prompts otimizados para o modelo de linguagem configurado.
5. **Envio de Resposta**: Após a geração da resposta, a mensagem é enviada ao usuário via API do WhatsApp.

## Tecnologias Utilizadas

- **Python**: Linguagem principal para desenvolvimento.
- **Flask**: Framework web para criação do webhook.
- **ngrok**: Para expor o servidor local ao público.
- **Facebook Graph API**: Integração com o WhatsApp.
- **Google Generative AI**: Para geração de respostas dinâmicas.
- **Pandas**: Gerenciamento de dados estruturados (produtos e serviços).
- **CrewAI**: Coordenação dos agentes inteligentes.

## Configuração e Execução

1. **Clonar o Repositório**:
   ```bash
   git clone https://github.com/CarlosArantes53/Auto_agent.git
   cd seu-repositorio
2. **Instalar Dependências: Utilize um ambiente virtual para gerenciar as dependências**:
   ```bash
   python -m venv venv
   source  venv\Scripts\activate
   pip install -r requirements.txt

4. **Configurar Variáveis de Ambiente: Crie um arquivo .env e configure as variáveis necessárias:**
  ACCESS_TOKEN=your_whatsapp_api_access_token
  PHONE_ID=your_phone_number_id
  VERIFY_TOKEN=your_webhook_verify_token
  GOOGLE_API_KEY=your_google_api_key

5. **Iniciar o Servidor: Execute a aplicação localmente:**
   python run.py
   
7. **Expor o Webhook com ngrok: Inicie o ngrok para expor o webhook:**
   ngrok http 5000 --domain (seu dominio)

Referências e link úteis:
-> Gerar "ACCESS_TOKEN" : https://developers.facebook.com/apps/

-> Gerar e configurar todo ngrok : https://dashboard.ngrok.com/domains/

-> Gerar gemini api : https://aistudio.google.com/app/u/1/apikey

-> Repositórios e tutoriais utilizados como referências:
--> https://github.com/alexfazio/crewAI-quickstart/blob/main/crewai_sequential_YoutubeVideoSearchTool_quickstart.ipynb

--> https://www.youtube.com/watch?v=3YPeh-3AFmM&t=359s

--> https://github.com/daveebbelaar/python-whatsapp-bot/tree/main

**Exemplos de app respondendo WhatsApp, vide que o mesmo sabe identificar quando não se trata de um animal, sabe identificar fotos e interpretar áudios**


![Captura de tela 2024-12-12 093538](https://github.com/user-attachments/assets/427ef73f-6392-43fe-b53c-90ea983401ad)


![Captura de tela 2024-12-12 093529](https://github.com/user-attachments/assets/cb8fd590-d3b9-4d83-b47b-264de01986c5)


![Captura de tela 2024-12-12 093520](https://github.com/user-attachments/assets/637c8b00-b0c0-4f66-b350-3a432be18b8e)
