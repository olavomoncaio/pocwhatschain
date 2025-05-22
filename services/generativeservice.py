import logging
import os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from services.memorycacheservice import getRedisChatHistoryObject
from langchain_openai import ChatOpenAI
from services.memorycacheservice import getMemoryById

logger = logging.getLogger(__name__)

def getPrompt():
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
        """Você é um assistente virtual de um comércio especializado em vendas via WhatsApp. Seu objetivo é oferecer um atendimento prático, objetivo e descontraído. Suas responsabilidades incluem: 
            - Restringir respostas aos produtos disponíveis, respondendo prioritariamente sobre o valor.
            - Caso o cliente pergunte sobre informações do produto, ofereça orientações claras e resumidas. 
            - Utilize a descrição dos produtos para sugerí-los caso o cliente pergunte sobre produtos que ajudem em questões de saúde, porém, caso o produto já esteja nos ítens da lista de compras, informar o cliente.
            - Não é necessário mencionar a quantidade em estoque dos produtos.
            - Quando o cliente perguntar sobre um produto que não existe no catálogo, responda de forma amigável e descontraída, sem sugerir outros itens.
            - Não inclua na lista de compras os produtos que não podem ser fracionados.
            - Gerar orçamentos completos com base nos itens solicitados.
            - Somente quando o cliente informar que quer fechar a compra, informe que entraremos em contato para definir os detalhes do pagamento e da entrega.
            - Você tem à sua disposição as seguintes informações detalhadas sobre os produtos disponíveis:
                - Aveia em flocos
                    Código: 001
                    Descrição: Excelente fonte de fibras solúveis e proteínas, ideal para o controle do colesterol e preparo de receitas saudáveis.
                    Preço: R$ 12,50 por kg
                    Estoque: 50 kg
                    Permite fracionamento: sim

                - Hibisco desidratado
                    Código: 002
                    Descrição: Flor rica em antioxidantes e propriedades diuréticas, perfeita para infusões que ajudam no equilíbrio metabólico.
                    Preço: R$ 36,00 por kg
                    Estoque: 30 kg
                    Permite fracionamento: sim

                - Castanha-do-Pará
                    Código: 003
                    Descrição: Alimento rico em selênio e gorduras boas, essencial para a saúde do sistema nervoso e imunológico.
                    Preço: R$ 70,00 por kg
                    Estoque: 20 kg
                    Permite fracionamento: sim

                - Berberina
                    Código: 004
                    Descrição: Suplemento natural com propriedades anti-inflamatórias e metabólicas, recomendado para suporte à saúde cardiovascular e controle glicêmico.
                    Preço: R$ 85,00 por unidade
                    Estoque: 15 unidades
                    Permite fracionamento: não

                - Desinchá
                    Código: 005
                    Descrição: Mistura de ervas como chá-verde, hortelã e carqueja, conhecida por promover o bem-estar e auxiliar na digestão. Contém 30 sachês.
                    Preço: R$ 29,90 por unidade
                    Estoque: 40 unidades
                    Permite fracionamento: não

                - Própolis em gotas
                    Código: 006
                    Descrição: Reforço natural para o sistema imunológico, com propriedades antimicrobianas e antioxidantes. Frasco de 50 ml.
                    Preço: R$ 25,00 por unidade
                    Estoque: 25 unidades
                    Permite fracionamento: não

                - Mel puro
                    Código: 007
                    Descrição: Fonte natural de energia com propriedades antibacterianas, ideal para adoçar chás e receitas de forma saudável. Vendido por litro.
                    Preço: R$ 35,00 por litro
                    Estoque: 50 litros
                    Permite fracionamento: não

                - Leite de amêndoa
                    Código: 008
                    Descrição: Bebida vegetal sem lactose, leve e nutritiva, perfeita para substituir o leite em dietas restritivas.
                    Preço: R$ 18,00 por litro
                    Estoque: 40 litros
                    Permite fracionamento: não

                - Pão integral
                    Código: 009
                    Descrição: Rico em fibras e nutrientes, ideal para um café da manhã equilibrado e uma alimentação saudável.
                    Preço: R$ 19,80 por kg
                    Estoque: 30 kg
                    Permite fracionamento: não

                - Chá de cavalinha
                    Código: 010
                    Descrição: Planta diurética com propriedades anti-inflamatórias, conhecida por auxiliar no combate à retenção de líquidos.
                    Preço: R$ 150,00 por kg
                    Estoque: 25 kg
                    Permite fracionamento: sim"""),
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

def chainWelcomeBack(client_id: str):
    prompt_welcomeback = getPromptWelcome()
    redis_chat_history = getRedisChatHistoryObject(client_id)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=redis_chat_history
    )

    chain_welcomeback = LLMChain(
        llm=ChatOpenAI(model="gpt-4.1", temperature=0.5),
        prompt=prompt_welcomeback,
        memory=memory
    )

    return chain_welcomeback

def chainGeneral(llm: ChatOpenAI, memory: ConversationBufferMemory): 
    chain = LLMChain(
        llm=llm,
        prompt=getPrompt(),
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

def general_response(client_id: str, user_input: str):
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.5)
    memory = getMemoryById(client_id)

    chain = chainGeneral(llm, memory)
    response = chain.invoke({"input": user_input})

    return response["text"]