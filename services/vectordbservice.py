from langchain_community.llms import OpenAI
from langchain_community.vectorstores import Weaviate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import weaviate
import logging

load_dotenv()
logger = logging.getLogger(__name__)

## Conecta com o banco vetorial Weavite
def vectordb_connect():
    logger.info(f"Iniciando get_vectorstore.")
    # Conectar ao Weaviate
    client = weaviate.Client(
        url=os.getenv("RAILWAYWEAVITE"),  # URL como string
        additional_headers={
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
        }
    )

    return client

## Retorna a instância do vectorstore
def get_vectorstore():
    logger.info(f"Iniciando get_vectorstore.")
    # Acessando o índice existente
    vectorstore = Weaviate(
        client=vectordb_connect(),
        index_name="EasyAI",
        text_key="texto",      # Ajuste conforme o nome do campo do índice
        embedding=OpenAIEmbeddings(),   #None quando não for busca vetorial
        by_text=False          # Quando for fazer busca por vetores é igual a False
    )

    logger.info(f"Finalizando get_vectorstore.")
    return vectorstore

## Buscar produtos relevantes no Weaviate
def get_retriever(vectorstore):
    logger.info(f"Iniciando get_retriver.")
    retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}  # Retorna os 3 produtos mais relevantes
    )

    logger.info(f"Finalizando get_retriver.")
    return retriever