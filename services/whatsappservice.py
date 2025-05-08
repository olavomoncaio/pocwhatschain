import httpx
import logging
import os

logger = logging.getLogger(__name__)

async def send_callback_whatsapp(message: str):
    logger.info(f"Enviando callback para whatsapp {message}")
    url = os.getenv("API_MOCK")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            return data

    except Exception as e:
        logger.info(f"Enviando callback para whatsapp {message}")
        return False