import logging
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from services.memorycacheasyncservice import get_key, get_memory_by_id
from services.estoqueservice import EstoqueService
from models.models import get_db
from utils.estoqueformatter import format_estoque
from datetime import datetime

logger = logging.getLogger(__name__)

def getPrompt(phone_enterprise: str):
    logger.info(f"Obtendo estoque Redis {datetime.now()}")
    estoqueKey = f"estoque:{phone_enterprise}"
    estoque = get_key(estoqueKey)
    logger.info(f"Estoque obtido Redis {datetime.now()}")

    if estoque is None:
        logger.info(f"Obtendo estoque postgreSQL {datetime.now()}")
        db = next(get_db())
        estoque_service = EstoqueService(db) 
        estoque = estoque_service.obter_estoque(phone_enterprise) 
        logger.info(f"Estoque obtido PostgreSQL {datetime.now()}")
    
    estoqueFormatted = format_estoque(estoque)

    systemPromptText = f"""Você é um assistente virtual de um comércio especializado em vendas via WhatsApp. Seu objetivo é oferecer um atendimento prático, objetivo e descontraído. Suas responsabilidades incluem: 
            - Restringir respostas aos produtos disponíveis, respondendo prioritariamente sobre o valor.
            - Caso o cliente pergunte sobre informações do produto, ofereça orientações claras e resumidas. 
            - Utilize a descrição dos produtos para sugerí-los caso o cliente pergunte sobre produtos que ajudem em questões de saúde, porém, caso o produto já esteja nos ítens da lista de compras, informar o cliente.
            - Não é necessário mencionar a quantidade em estoque dos produtos.
            - Quando o cliente perguntar sobre um produto que não existe no catálogo, responda de forma amigável e descontraída, sem sugerir outros itens.
            - Não inclua na lista de compras os produtos que não podem ser fracionados.
            - Gerar orçamentos completos com base nos itens solicitados.
            - Somente quando o cliente informar que quer fechar a compra, informe que entraremos em contato para definir os detalhes do pagamento e da entrega.
            - Você tem à sua disposição as seguintes informações detalhadas sobre os produtos disponíveis:
                {estoqueFormatted}"""  

    prompt = ChatPromptTemplate.from_messages([
       ("system", 
        systemPromptText),
        MessagesPlaceholder(variable_name="chat_history", n_messages=20),
        ("human", "{input}")
    ])

    return prompt

def getPromptWelcome():
    prompt_welcomeback = ChatPromptTemplate([
    ("system", 
     """O cliente com nome {input} está retornando ao WhatsApp do estabelecimento para continuar a compra:
            - Pergunte explicitamente, de forma curta e descontraída, se ele quer continuar com a comprar anterior. 
            - Utilize a memória apenas para listar os itens que o cliente já havia incluído na lista
            - Pergunta se ele quer continuar a compra anterior, respondendo sim ou não"""),
    MessagesPlaceholder(variable_name="chat_history", n_messages=20)        
    ])

    return prompt_welcomeback

def getPromptPlaceAnOrder():
    prompt_placeanorder = ChatPromptTemplate([
    ("system", 
     """O cliente com nome {input} fechando o pedido:
            - Mostre uma frase curta e descontraída agradecendo pelo pedido. 
            - Utilize a memória apenas para listar os itens da lista do pedido
            - Informe que entraremos em contato para definir os detalhes do pagamento e da entrega."""),
    MessagesPlaceholder(variable_name="chat_history", n_messages=20)        
    ])
    return prompt_placeanorder

def chainGeneral(llm: ChatOpenAI, memory: ConversationBufferMemory, phone_enterprise: str): 
    chain = LLMChain(
        llm=llm,
        prompt=getPrompt(phone_enterprise),
        memory=memory
    )

    return chain

def chainPlaceAnOrder(llm: ChatOpenAI, memory: ConversationBufferMemory): 
    chain = LLMChain(
        llm=llm,
        prompt=getPromptPlaceAnOrder(),
        memory=memory
    )

    return chain

def classify_client_response(response_text):
    classification_prompt = """
    Analise a seguinte resposta do cliente a uma pergunta sobre continuar uma compra anterior.
    Classifique a intenção do cliente em:
    - 'sim' (inclui respostas afirmativas como "sim", "quero", "pode ser", "claro", etc.)
    - 'não' (inclui respostas negativas como "não", "não quero", "melhor não", "finalizar pedido", "fechar compra", etc.)
    - 'fechar' (inclui respostas como "quero fechar a compra", "finalizar comprar", "fechar pedido", "finalizar pedido", "fechar compra", etc.)
    
    Considere o contexto: o cliente está sendo perguntado se deseja continuar uma compra anterior em um chat de WhatsApp.
    
    Resposta do cliente: "{response_text}"
    
    Retorne apenas 'sim' ou 'não', sem aspas, pontuação ou explicações.
    """
    
    classification_llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    classification = classification_llm.invoke(classification_prompt.format(response_text=response_text))
    
    return classification.content.lower().strip()

def general_response(client_id: str, user_input: str, phone_enterprise: str):
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.5)
    memory = get_memory_by_id(client_id)

    chain = chainGeneral(llm, memory, phone_enterprise)
    logger.info(f"Invocando Chain {datetime.now()}")
    response = chain.invoke({"input": user_input})
    logger.info(f"Finalizando Chain {datetime.now()}")

    return response["text"]