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
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    vectorstore = get_vectorstore()
except Exception as e:
    logger.error(f"Falha ao iniciar o vectorstore: {str(e)}")
    raise

# LLM e Prompt
def getPromptRAG(context: str) -> ChatPromptTemplate:

    systemPromptText = f"""Você é um assistente virtual de um comércio especializado em vendas via WhatsApp. Seu objetivo é oferecer um atendimento prático, objetivo e descontraído. Suas responsabilidades incluem: 
    - Restringir respostas aos produtos disponíveis, respondendo prioritariamente sobre o valor.
    - O estabelecimento não oferece cupons de desconto, responda de formar curta e bem descontraída caso o cliente pergunte.
    - Os valores dos produtos são os que estão no cadastro, e somento os valores do cadastro devem ser utilizados. 
    - Caso o cliente pergunte sobre informações do produto, ofereça orientações claras e resumidas, sempre citando o nome do produto. 
    - Utilize a descrição dos produtos para sugerí-los caso o cliente pergunte sobre produtos que ajudem em questões de saúde, porém, caso o produto já esteja nos ítens da lista de compras, informar o cliente.
    - Não é necessário mencionar a quantidade em estoque dos produtos.
    - Quando o cliente perguntar sobre um produto que não existe no catálogo, responda de forma amigável e descontraída, sem sugerir outros itens.
    - Não inclua na lista de compras os produtos que não podem ser fracionados.
    - Gerar orçamentos completos com base nos itens solicitados.
    - Somente quando o cliente informar que quer fechar a compra, informe que entraremos em contato para definir os detalhes do pagamento e da entrega.
    - Contexto relevant sobre os produtos: \n {context}"""  

    return ChatPromptTemplate.from_messages([
       ("system", 
        systemPromptText),
        MessagesPlaceholder(variable_name="chat_history", n_messages=20),
        ("human", "{input}")
    ])


## Buscar produtos relevantes no Weaviate
def generate_context(user_input: str) -> str:
    try:
        relevant_docs = get_retriever(vectorstore).invoke(user_input)
        return "\n".join(doc.page_content for doc in relevant_docs)
    except Exception as e:
        logger.error(f"Erro ao gerar o contexto: {str(e)}")
        return ""


## Chain com a implementação do RAG
def chain_response(memory, llm, prompt, user_input):
    chat_history = memory.buffer if hasattr(memory, 'buffer') else [] # Isso já retorna a lista de HumanMessage/AIMessage
    chain = (
        {"context": generate_context(user_input), "input": RunnablePassthrough(), "chat_history": lambda x: chat_history}  # Passa a lista diretamente
        | prompt 
        | llm
    )
    # Executa a chain
    result = chain.invoke(user_input)
    # Atualiza a memória
    memory.save_context({"input": user_input}, {"output": result.content})
    
    return result.content


## Execução geral da resposta generativa utilizando a técnica de RAG
def general_responseRAG(client_id: str, user_input: str, phone_enterprise: str):
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.5)
    memory = get_memory_by_id(client_id)
    context = generate_context(user_input)
    prompt=getPromptRAG(context)
    logger.info(f"Invocando Chain RAG {datetime.now()}")
    response = chain_response(memory, llm, prompt, user_input)
    logger.info(f"Finalizando Chain RAG{datetime.now()}")

    return response

