import logging
import redis

logger = logging.getLogger(__name__)

# Conexão global (reutilizável) - ajuste host se necessário
redis_client = redis.Redis(
    host="localhost",  # No Docker Compose, use "redis" como host
    port=6379,
    decode_responses=True  # Converte automaticamente para string
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