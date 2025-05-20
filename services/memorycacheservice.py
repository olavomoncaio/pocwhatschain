import logging
import redis
from langchain.memory import ConversationBufferMemory, RedisChatMessageHistory

logger = logging.getLogger(__name__)

# Conexão global (reutilizável) - ajuste host se necessário
redis_client = redis.Redis(
    host="localhost",  # No Docker Compose, use "redis" como host
    port=6379
)

def getKey(key: str):
    logger.info(f"Obtendo chave {key} do Redis")
    try:
        resultado = redis_client.get(key)  # Sem chaves {}
        return resultado
    except Exception as e:
        logger.error(f"Erro ao obter chave do Redis: {e}")
        return None  # Melhor que False para diferenciar de "não encontrado"

def setKey(key: str, value: str):
    logger.info(f"Salvando chave {key} no Redis")
    try:
        redis_client.set(key, value)  # Sem chaves {}
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar no Redis: {e}")
        return False
    


    
    
def verifyPreviousConversations(client_id: str):
    redis_chat_history = getRedisChatHistoryObject(client_id)

    has_previous_conversation = len(redis_chat_history.messages) > 0
    return has_previous_conversation

def clear_memory(client_id: str):
    redis_chat_history = getRedisChatHistoryObject(client_id)
    redis_chat_history.clear()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=redis_chat_history
    )

    return memory

def getMemoryById(client_id: str):
    redis_chat_history = getRedisChatHistoryObject(client_id)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=redis_chat_history
    )

    return memory

# Obter objeto padrão do RedisChatMessageHistory
def getRedisChatHistoryObject(client_id: str):
    redis_chat_history = RedisChatMessageHistory(
        url="localhost:6379", 
        session_id=client_id 
    )

    return redis_chat_history