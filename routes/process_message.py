from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.generativeservice import chainWelcomeBack, classify_client_response, chainPlaceAnOrder, general_response
from services.memorycacheservice import verifyPreviousConversations, clear_memory
from services.whatsappservice import send_callback_whatsapp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TextMessage(BaseModel):
    message: str

class ReceivedCallbackModel(BaseModel):
    isStatusReply: bool
    chatLid: str
    connectedPhone: str
    waitingMessage: bool
    isEdit: bool
    isGroup: bool
    isNewsletter: bool
    instanceId: str
    messageId: str
    phone: str
    fromMe: bool
    momment: int
    status: str
    chatName: str
    senderPhoto: Optional[str] = None
    senderName: str
    photo: Optional[str] = None
    broadcast: bool
    participantLid: Optional[str] = None
    forwarded: bool
    type: str
    fromApi: bool
    text: TextMessage

@router.post("/process_message")
async def process_message(req: ReceivedCallbackModel):
    try:
        resposta = ""
        logger.info(f"Requisição recebida: {req.model_dump()}")

        resposta = general_response(req.phone, req.text.message)      

        callbackResult = await send_callback_whatsapp(resposta, req.phone)
        logger.info(f"Processamento finalizado com sucesso para o cliente {req.phone} - CallbackResult: {callbackResult} - Resposta: {resposta}")

        resultado = {
            "status": callbackResult,
            "message": resposta
        }

        return resultado

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")
