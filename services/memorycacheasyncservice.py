import logging
from langchain.memory import ConversationBufferMemory, RedisChatMessageHistory
import redis
from datetime import datetime
from typing import Optional, Any
import contextlib

logger = logging.getLogger(__name__)

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "socket_timeout": 5,
    "socket_connect_timeout": 2,
    "max_connections": 10
}

_redis_pool = redis.ConnectionPool(**REDIS_CONFIG)
 
def get_redis_connection() -> redis.Redis:
    return redis.Redis(connection_pool=_redis_pool)

@contextlib.contextmanager
def redis_connection():
    conn = get_redis_connection()
    try:
        yield conn
    finally:
        conn.close() 

def verify_previous_conversations(client_id: str) -> bool:
    try:
        with redis_connection() as conn:
            exists = conn.exists(f"message_store:{client_id}") > 0
            logger.info(f"Verificação de conversa existente para {client_id}: {exists}")
            return exists
    except Exception as e:
        logger.error(f"Erro ao verificar conversas: {e}", exc_info=True)
        return False

def clear_memory(client_id: str) -> ConversationBufferMemory:
    try:
        with redis_connection() as conn:
            conn.delete(f"message_store:{client_id}")
            logger.info(f"Memória limpa para {client_id}")
            
        return get_memory_by_id(client_id)
    except Exception as e:
        logger.error(f"Erro ao limpar memória: {e}", exc_info=True)
        raise

def get_memory_by_id(client_id: str) -> ConversationBufferMemory:
    start_time = datetime.now()
    logger.info(f"Iniciando obtenção de memória para {client_id}")
    
    try:
        redis_chat_history = RedisChatMessageHistory(
            url="redis://localhost:6379", 
            session_id=client_id
        )
        
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=redis_chat_history
        )
        
        logger.info(f"Memória obtida para {client_id} em {(datetime.now() - start_time).total_seconds():.3f}s")
        return memory
    except Exception as e:
        logger.error(f"Erro ao obter memória: {e}", exc_info=True)
        raise

def get_key(key: str) -> Optional[Any]:
    start_time = datetime.now()
    logger.info(f"Obtendo chave {key}")
    
    try:
        with redis_connection() as conn:
            result = conn.get(key)
            logger.info(f"Chave {key} obtida em {(datetime.now() - start_time).total_seconds():.3f}s")
            return result
    except Exception as e:
        logger.info(f"Erro ao obter chave {key}: {e}", exc_info=True)
        return None

def set_key(key: str, value: str, ttl: Optional[int] = None) -> bool:
    start_time = datetime.now()
    logger.info(f"Definindo chave {key}")
    
    try:
        with redis_connection() as conn:
            if ttl:
                conn.setex(key, ttl, value)
            else:
                conn.set(key, value)
                
            logger.info(f"Chave {key} definida em {(datetime.now() - start_time).total_seconds():.3f}s")
            return True
    except Exception as e:
        logger.error(f"Erro ao definir chave {key}: {e}", exc_info=True)
        return False