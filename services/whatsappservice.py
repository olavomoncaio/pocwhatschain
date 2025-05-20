import httpx
import logging
import os

logger = logging.getLogger(__name__)

async def send_callback_whatsapp(resposta: str, phone: str):
    logger.info(f"Enviando callback para whatsapp {phone}")
    url = os.getenv("ZAPI_URL")
    token = os.getenv("ZAPI_TOKEN")

    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "phone": phone,
                "message": resposta
            }, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            })

    except Exception as e:
        logger.error(f"Erro ao enviar callback para whatsapp {phone}")
        return False