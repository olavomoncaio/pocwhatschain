import httpx
import logging
import os

logger = logging.getLogger(__name__)

async def send_message_openai(message: str):
    logger.info(f"Enviando requisição para openia {message}")
    url = os.getenv("API_MOCK")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            return data

    except Exception as e:
        logger.info(f"Ocorreu um erro para enviar a requisição {e}")
        return False