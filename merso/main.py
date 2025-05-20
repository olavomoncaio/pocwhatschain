from langchain_community.document_loaders import JSONLoader
from langchain_community.llms import OpenAI
from langchain_community.vectorstores import Weaviate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, RedisChatMessageHistory
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import weaviate

load_dotenv()

# Conectar ao Weaviate
# client = weaviate.Client(
#     "http://localhost:8080",  # URL como string
#     additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
# )

# Acessando o índice existente
# vectorstore = Weaviate(
#     client=client,
#     index_name="EasyAI",
#     text_key="product",      # Ajuste conforme o nome do campo no seu índice
#     attributes=["product"],  # Campos adicionais para recuperar
#     embedding=OpenAIEmbeddings(),   #None quando não for busca vetorial
#     by_text=False          # Quando for fazer busca por vetores é igual a False
# )

# Configuração do Redis
redis_url = os.getenv("REDIS_URL")
SESSION_ID = "unique_session_id"  # Identificador único para armazenar/recuperar histórico
                                  # A composição da chave fica "message_store:<unique_session_id>

# Função para limpar a memória
def clear_memory(): 
    global memory, redis_chat_history
    redis_chat_history.clear()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=redis_chat_history
    )

# Configurar histórico no Redis
redis_chat_history = RedisChatMessageHistory(
    url=redis_url,
    session_id=SESSION_ID  # Usado como chave no Redis
)

has_previous_conversation = len(redis_chat_history.messages) > 0

# LLM e Prompt
llm = ChatOpenAI(model="gpt-4.1", temperature=0.5)
llm_utils = ChatOpenAI(model="gpt-4.1", temperature=0.0)

prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """Você é um assistente virtual de um comércio especializado em vendas via WhatsApp. Seu objetivo é oferecer um atendimento prático, objetivo e descontraído. Suas responsabilidades incluem: 
        - Restringir respostas aos produtos disponíveis, respondendo prioritariamente sobre o valor.
        - Caso o cliente pergunte sobre informações do produto, ofereça orientações claras e resumidas. 
        - Utilize a descrição dos produtos para sugerí-los caso o cliente pergunte sobre produtos que ajudem em questões de saúde, porém, caso o produto já esteja nos ítens da lista de compras, informar o cliente.
        - Não é necessário mencionar a quantidade em estoque dos produtos.
        - Gerar orçamentos completos com base nos itens solicitados.
        - Quando o cliente perguntar sobre um produto que não existe no catálogo, responda de forma amigável e descontraída, sem sugerir outros itens.
        - Somente quando o cliente informar que quer fechar a compra, informe que entraremos em contato para definir os detalhes do pagamento e da entrega.
        - Você tem à sua disposição as seguintes informações detalhadas sobre os produtos disponíveis:
            - Aveia em flocos
                Código: 001
                Descrição: Excelente fonte de fibras solúveis e proteínas, ideal para o controle do colesterol e preparo de receitas saudáveis.
                Preço: R$ 12,50 por kg
                Estoque: 50 kg

            - Hibisco desidratado
                Código: 002
                Descrição: Flor rica em antioxidantes e propriedades diuréticas, perfeita para infusões que ajudam no equilíbrio metabólico.
                Preço: R$ 36,00 por kg
                Estoque: 30 kg

            - Castanha-do-Pará
                Código: 003
                Descrição: Alimento rico em selênio e gorduras boas, essencial para a saúde do sistema nervoso e imunológico.
                Preço: R$ 70,00 por kg
                Estoque: 20 kg

            - Berberina
                Código: 004
                Descrição: Suplemento natural com propriedades anti-inflamatórias e metabólicas, recomendado para suporte à saúde cardiovascular e controle glicêmico.
                Preço: R$ 85,00 por unidade
                Estoque: 15 unidades

            - Desinchá
                Código: 005
                Descrição: Mistura de ervas como chá-verde, hortelã e carqueja, conhecida por promover o bem-estar e auxiliar na digestão. Contém 30 sachês.
                Preço: R$ 29,90 por unidade
                Estoque: 40 unidades

            - Própolis em gotas
                Código: 006
                Descrição: Reforço natural para o sistema imunológico, com propriedades antimicrobianas e antioxidantes. Frasco de 50 ml.
                Preço: R$ 25,00 por unidade
                Estoque: 25 unidades

            - Mel puro
                Código: 007
                Descrição: Fonte natural de energia com propriedades antibacterianas, ideal para adoçar chás e receitas de forma saudável. Vendido por litro.
                Preço: R$ 35,00 por litro
                Estoque: 50 litros

            - Leite de amêndoa
                Código: 008
                Descrição: Bebida vegetal sem lactose, leve e nutritiva, perfeita para substituir o leite em dietas restritivas.
                Preço: R$ 18,00 por litro
                Estoque: 40 litros

            - Pão integral
                Código: 009
                Descrição: Rico em fibras e nutrientes, ideal para um café da manhã equilibrado e uma alimentação saudável.
                Preço: R$ 19,80 por kg
                Estoque: 30 kg

            - Chá de cavalinha
                Código: 010
                Descrição: Planta diurética com propriedades anti-inflamatórias, conhecida por auxiliar no combate à retenção de líquidos.
                Preço: R$ 150,00 por kg
                Estoque: 25 kg"""),
    MessagesPlaceholder(variable_name="chat_history", n_messages=20),
    ("human", "{input}")
])

prompt_welcomeback = ChatPromptTemplate([
    ("system", 
     """O cliente com nome {input} está retornando ao WhatsApp do estabelecimento para continuar a compra:
            - Pergunte explicitamente, de forma curta e descontraída, se ele quer continuar com a comprar anterior. 
            - Utilize a memória apenas para listar os itens que o cliente já havia incluído na lista
            - Pergunta se ele quer continuar a compra anterior, respondendo sim ou não"""),
    MessagesPlaceholder(variable_name="chat_history", n_messages=20)        
])

prompt_placeanorder = ChatPromptTemplate([
    ("system", 
     """O cliente com nome {input} fechando o pedido:
            - Mostre uma frase curta e descontraída agradecendo pelo pedido. 
            - Utilize a memória apenas para listar os itens da lista do pedido
            - Informe que entraremos em contato para definir os detalhes do pagamento e da entrega."""),
    MessagesPlaceholder(variable_name="chat_history", n_messages=20)        
])

# Cria a chain com memória
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    chat_memory=redis_chat_history
)

# Cadeia com memória persistente
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    memory=memory
    # verbose=True
)

# Cadeia com memória persistente welcomeback
chain_welcomeback = LLMChain(
    llm=llm_utils,
    prompt=prompt_welcomeback,
    memory=memory
    # verbose=True
)

# Cadeia com memória persistente placeanorder
chain_placeanorder = LLMChain(
    llm=llm_utils,
    prompt=prompt_placeanorder,
    memory=memory
    # verbose=True
)

# retriever = vectorstore.as_retriever(
#     search_type="similarity",
#     search_kwargs={"k": 2}  # Retorna os 3 produtos mais relevantes
# )

# def generate_response(user_input):
#     # Buscar produtos relevantes no Weaviate
#     relevant_docs = retriever.invoke(user_input)
#     context = "\n".join([doc.page_content for doc in relevant_docs])
#     return context

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

def general_response(user_input):
    response = chain.invoke({"input": user_input})
    print("Resposta:", response["text"])
    first_interaction = False
    return response

print("Digite 'sair' para encerrar.")
first_interaction = True

while True:
    try:
        if first_interaction and has_previous_conversation:
            nome_cliente = "Emerson"
            welcome_message = chain_welcomeback.invoke({"input": nome_cliente})
            user_input = input(welcome_message["text"] + "\n>> ")
            
            # Classifica a resposta do cliente
            classification = classify_client_response(user_input)
            
            if classification in ['não', 'nao', 'n']:
                clear_memory()
                print("OK, vamos iniciar um novo atendimento. Como posso ajudar?")
            elif classification in ['fechar']:
                placeanorder_message = chain_placeanorder.invoke({"input": nome_cliente})
                print(placeanorder_message["text"] + "\n>> ")
                break
            else:
                general_response(user_input)
                
            first_interaction = False
            continue
            
        user_input = input(">> ")
        if user_input.lower() in ['sair', 'exit']:
            break
            
        general_response(user_input)
        
    except KeyboardInterrupt:
        print("\nEncerrando...")
        break