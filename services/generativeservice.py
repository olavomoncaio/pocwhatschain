import logging
import os
from langchain.chat_models import ChatOpenAI  # Alterado para ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

template = "Você é um agente que informa se determinado item existe no estoque, e se sim, você fala o preço. Estoque:\n{estoque}\n\n Pergunta do usuário: {pergunta}"
prompt = PromptTemplate(input_variables=["pergunta", "estoque"], template=template)

# Verifica se a chave API existe


async def send_message_openai(message: str):
    logger.info(f"Enviando requisição para openia {message}")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=openai_api_key)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    estoque = """
    Estoque atual:
    - Alface crespa (unidade) - R$ 3,50
    - Tomate italiano (kg) - R$ 7,80
    - Batata inglesa (kg) - R$ 4,90
    - Cenoura (kg) - R$ 5,20
    - Abobrinha verde (kg) - R$ 6,30
    - Brócolis ninja (unidade) - R$ 4,70
    - Couve-flor (unidade) - R$ 6,90
    - Espinafre (maço) - R$ 3,90
    - Rúcula (maço) - R$ 4,20
    - Pepino japonês (kg) - R$ 5,10
    - Pimentão vermelho (kg) - R$ 8,50
    - Pimentão verde (kg) - R$ 6,90
    - Cebola roxa (kg) - R$ 5,60
    - Cebola amarela (kg) - R$ 4,80
    - Alho (100g) - R$ 3,20
    - Chuchu (kg) - R$ 3,90
    - Mandioquinha (kg) - R$ 9,80
    - Inhame (kg) - R$ 6,40
    - Beterraba (kg) - R$ 4,30
    - Quiabo (kg) - R$ 7,10

    """

    # Adicionado await e usando chain.arun() para chamadas assíncronas
    resposta = await chain.arun(estoque=estoque, pergunta=message)
    return resposta