import os
from crewai import Agent, Task, Crew, Process, LLM
import pandas as pd
from crewai_tools import tool

my_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

try:
    with open("geral.txt", "r", encoding="utf-8") as f:
        geral_texto = f.read()
    produtos_df = pd.read_csv("produtos.csv")
    servicos_df = pd.read_csv("servicos.csv")
except FileNotFoundError as e:
    raise FileNotFoundError(f"Erro ao acessar arquivos: {e}")

@tool
def consultar_geral(pergunta: str) -> str:
    """Consulta informações gerais no texto carregado do arquivo geral.txt.
    
    Argumentos:
        pergunta (str): A pergunta feita pelo usuário.
    
    Retorna:
        str: Resposta baseada no conteúdo do arquivo geral.txt.
    """
    return geral_texto


@tool
def recomendar_produto(preferencia: str) -> str:
    """Recomenda produtos com base na preferência do usuário e no catálogo de produtos.
    
    Argumentos:
        preferencia (str): A categoria ou característica do produto preferido.
    
    Retorna:
        str: Recomendações ou uma mensagem indicando que não há produtos disponíveis.
    """
    if produtos_df.empty:
        return "Catálogo de produtos indisponível. Verifique o arquivo produtos.csv."
    recomendacoes = produtos_df[produtos_df['Categoria'].str.contains(preferencia, na=False)]
    if recomendacoes.empty:
        return "Nenhum produto encontrado para essa preferência."
    prompt = f"""
    Baseado no seguinte catálogo de produtos:
    {recomendacoes.to_string(index=False)}

    Identifique os melhores produtos para pets que atendem à preferência: {preferencia}.
    """
    return my_llm.generate(prompt)


@tool
def recomendar_servico(preferencia: str) -> str:
    """Recomenda serviços com base na preferência do usuário e no catálogo de serviços.
    
    Argumentos:
        preferencia (str): A categoria ou tipo de serviço preferido.
    
    Retorna:
        str: Recomendações ou uma mensagem indicando que não há serviços disponíveis.
    """
    if servicos_df.empty:
        return "Catálogo de serviços indisponível. Verifique o arquivo servicos.csv."
    recomendacoes = servicos_df[servicos_df['Categoria'].str.contains(preferencia, na=False)]
    if recomendacoes.empty:
        return "Nenhum serviço encontrado para essa preferência."
    prompt = f"""
    Baseado no seguinte catálogo de serviços:
    {recomendacoes.to_string(index=False)}

    Identifique os melhores serviços para pets que atendem à preferência: {preferencia}.
    """
    return my_llm.generate(prompt)

central_agent = Agent(
    role="Atendente Central",
    goal="Fornecer respostas detalhadas sobre o PetShop Amigo Fiel, incluindo horário de atendimento, serviços, equipe e promoções.",
    backstory="Você é um atendente experiente do PetShop Amigo Fiel, altamente conhecedor das informações gerais da loja e sempre disposto a ajudar clientes a encontrar o que precisam para seus pets.",
    tools=[consultar_geral],
    llm=my_llm
)

produto_agent = Agent(
    role="Especialista em Produtos",
    goal="Recomendar os melhores produtos para pets com base nas preferências do cliente e no catálogo do PetShop Amigo Fiel.",
    backstory="Você é um especialista em produtos para pets no PetShop Amigo Fiel, com habilidades excepcionais para identificar os itens mais adequados às necessidades específicas de cada cliente e seus pets.",
    tools=[recomendar_produto],
    llm=my_llm
)

servico_agent = Agent(
    role="Especialista em Serviços",
    goal="Recomendar serviços adequados para pets com base no catálogo do PetShop Amigo Fiel e nas preferências do cliente.",
    backstory="Você é um especialista nos serviços oferecidos pelo PetShop Amigo Fiel, com um profundo conhecimento sobre como ajudar clientes a escolher os serviços ideais para seus pets.",
    tools=[recomendar_servico],
    llm=my_llm
)

tarefa_central = Task(
    description="Responder perguntas gerais do usuário baseadas no arquivo geral.txt",
    agent=central_agent,
    expected_output="Respostas claras e precisas para perguntas gerais."
)

tarefa_produto = Task(
    description="Recomendar produtos com base nas preferências do usuário.",
    agent=produto_agent,
    expected_output="Uma lista de produtos recomendados."
)

tarefa_servico = Task(
    description="Recomendar serviços com base nas preferências do usuário.",
    agent=servico_agent,
    expected_output="Uma lista de serviços recomendados."
)

crew = Crew(
    agents=[central_agent, produto_agent, servico_agent],
    tasks=[tarefa_central, tarefa_produto, tarefa_servico],
    verbose=True,
    process=Process.sequential
)