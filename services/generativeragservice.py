import logging
from typing import Optional
from services.memorycacheasyncservice import get_key, get_memory_by_id
from services.vectordbservice import get_retriever, vectordb_connect, get_vectorstore
from langchain_community.vectorstores import Weaviate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
import os
from operator import itemgetter
from datetime import datetime
from utils.estoqueformatter import format_estoque

logger = logging.getLogger(__name__)

try:
    vectorstore = get_vectorstore()
except Exception as e:
    logger.error(f"Falha ao iniciar o vectorstore: {str(e)}")
    raise

# LLM e Prompt
def getPromptRAG(context: str) -> ChatPromptTemplate:

    try:
        logger.info("Iniciando getPromptRAG")

         # Primeiro verifique o tipo e estrutura do context
        logger.info(f"Tipo do context: {type(context)}")
        logger.info(f"Exemplo do primeiro item: {context[0] if len(context) > 0 else 'vazio'}")
        
        # Se context for uma string JSON, precisamos parsear
        if isinstance(context, str):
            import json
            try:
                context = json.loads(context)
            except json.JSONDecodeError:
                context = []
        
        # Se for uma lista de strings JSON, parsear cada item
        if len(context) > 0 and isinstance(context[0], str):
            import json
            try:
                context = [json.loads(item) for item in context]
            except json.JSONDecodeError:
                context = []
        

        formatted_context = "\n".join(
            f"Produto: {item.get('nome', 'N/A')}\n"
            f"Código: {item.get('codigo', 'N/A')}\n"
            f"Preço: R${float(item.get('preco', 0)):.2f}\n"
            f"Unidade: {item.get('unidade', 'N/A')}\n"
            f"Descrição: {item.get('descricao', 'Sem descrição')}\n"
            f"Pode ser fracionado: {'Sim' if str(item.get('fragmentavel', 'Não')).lower() == 'sim' else 'Não'}\n"
            for item in context if isinstance(item, dict)  # Filtra apenas itens que são dicionários
        )
        
        systemPromptText = f"""Você é um assistente virtual de um comércio especializado em vendas via WhatsApp. Seu objetivo é oferecer um atendimento prático, objetivo e descontraído. Suas responsabilidades incluem: 
        - Restringir respostas aos produtos disponíveis, respondendo prioritariamente sobre o valor.
        - O estabelecimento não oferece cupons de desconto, responda de formar curta e bem descontraída caso o cliente pergunte.
        - Os valores dos produtos são os que estão no cadastro, e somente os valores do cadastro devem ser utilizados. 
        - Caso o cliente pergunte sobre informações do produto, ofereça orientações claras e resumidas, sempre citando o nome do produto. 
        - Utilize a descrição dos produtos para sugerí-los caso o cliente pergunte sobre produtos que ajudem em questões de saúde, porém, caso o produto já esteja nos ítens da lista de compras, informar o cliente.
        - Não é necessário mencionar a quantidade em estoque dos produtos.
        - Quando o cliente perguntar sobre um produto que não existe no catálogo, responda de forma amigável e descontraída, sem sugerir outros itens.
        - Não inclua na lista de compras os produtos que não podem ser fracionados.
        - Gerar orçamentos completos com base nos itens solicitados.
        - Somente quando o cliente informar que quer fechar a compra, informe que entraremos em contato para definir os detalhes do pagamento e da entrega.
        - Contexto relevante sobre os produtos: \n{formatted_context}"""

        logger.info(f"{systemPromptText}")
    
        prompt = ChatPromptTemplate.from_messages([
            ("system", systemPromptText),
            MessagesPlaceholder(variable_name="chat_history", n_messages=20),
            ("human", "{input}")
        ])
    except Exception as e:
        logger.error(f"Erro ao criar o prompt: {str(e)}")
        raise

    return prompt


## Buscar produtos relevantes no Weaviate
def generate_context(user_input: str) -> str:
    try:
        logger.error(f"Iniciando contexto {user_input}")
        relevant_docs = get_retriever(vectorstore).invoke(user_input)
        return "\n".join(doc.page_content for doc in relevant_docs)
    
    except Exception as e:
        logger.error(f"Erro ao gerar o contexto: {str(e)}") 
        return ""


## Chain com a implementação do RAG
def chain_response(memory, llm, prompt, user_input):
    try:
        # logger.info(f"Iniciando chain_response")
        # chat_history = memory.buffer if hasattr(memory, 'buffer') else [] # Isso já retorna a lista de HumanMessage/AIMessage
        # chain = (
        #     {"context": generate_context(user_input), "input": RunnablePassthrough(), "chat_history": lambda x: chat_history}  # Passa a lista diretamente
        #     | prompt 
        #     | llm
        # )
        # logger.info(f"Executando chain da string {user_input}")
        # result = chain.invoke(user_input)
        # logger.info(f"Iniciando save_Context")
        # memory.save_context({"input": user_input}, {"output": result.content})

        logger.info(f"Iniciando chain_response")
        
        # 1. Obter o histórico de chat corretamente
        chat_history = memory.load_memory_variables({}).get('history', []) if hasattr(memory, 'load_memory_variables') else []
        
        # 2. Criar a chain com a estrutura correta
        chain = (
            {
                "context": lambda x: generate_context(x["input"]),  # Função que recebe o input completo
                "input": itemgetter("input"),  # Pega especificamente o campo input
                "chat_history": itemgetter("chat_history")  # Pega especificamente o chat_history
            }
            | prompt
            | llm
        )
        
        logger.info(f"Executando chain da string {user_input}")
        
        # 3. Preparar os inputs no formato correto
        inputs = {
            "input": user_input,
            "chat_history": chat_history
        }
        
        result = chain.invoke(inputs)
        
        logger.info(f"Iniciando save_Context")
        memory.save_context({"input": user_input}, {"output": result.content})

    except Exception as e:
        logger.error(f"Erro ao executar a cadeia de RAG: {str(e)}")
        raise

    return result.content


## Execução geral da resposta generativa utilizando a técnica de RAG
def general_responseRAG(client_id: str, user_input: str, phone_enterprise: str):
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.5)
    memory = get_memory_by_id(client_id) 
    context = generate_context(user_input)
    prompt=getPromptRAG(context)
    logger.info(f"finalizando getPromptRAG")
    logger.info(f"Invocando Chain RAG {datetime.now()}")
    response = chain_response(memory, llm, prompt, user_input)
    logger.info(f"Finalizando Chain RAG{datetime.now()}")

    return response

