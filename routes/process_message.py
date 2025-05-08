from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.generativeservice import send_message_openai
from services.whatsappservice import send_callback_whatsapp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessMessageRequest(BaseModel):
    interactionId: str
    sessionId: str
    hashId: str
    message: Optional[str] = ""

@router.post("/process_message")
async def process_message(req: ProcessMessageRequest):
    try:
        logger.info(f"Requisição recebida: {req.model_dump()}")

        resposta = f"This is an echo message: {req.message}"

        openIaResponse = await send_message_openai(req.message)
        whatsappcallback = await send_callback_whatsapp(openIaResponse)

        logger.info(f"Processamento finalizado com sucesso para a interação {req.interactionId}")

        return {
            "interactionId": req.interactionId,
            "sessionId": req.sessionId,
            "hashId": req.hashId,
            "message": req.message,
            "resposta": resposta,
            "responseIntegration": openIaResponse
        }

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")