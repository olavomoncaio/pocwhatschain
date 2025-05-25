import json
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from services.generativeservice import general_response
from services.memorycacheasyncservice import get_key
from services.whatsappservice import send_callback_whatsapp
import logging
from datetime import datetime

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
        logger.info(f"Iniciando processo {datetime.now()}")
        resposta = ""
        phone_default = "5511982158891" ##telefone da loja
        clientKey = f"{phone_default}:{req.phone}"

        logger.info(f"Requisição recebida: {req.model_dump()}")

        resposta = general_response(clientKey, req.text.message, phone_default)      
        callbackResult = await send_callback_whatsapp(resposta, req.phone)
        logger.info(f"Processamento finalizado com sucesso para o cliente {req.phone} - Resposta: {resposta} - ClientKey: {clientKey}")

        resultado = {
            "status": callbackResult,
            "message": resposta
        }

        logger.info(f"Finalizando processo {datetime.now()}")
        return resultado

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")
    

@router.post("/getKey")
async def getKeyCache(key: str):
    try:
        logger.info(f"Requisição recebida getKey: {key}")

        redisResult = get_key(key)
    
        logger.info(f"Processamento finalizado com sucesso para obter chave")

        return {
            "resultado": redisResult
        }

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")

@router.post("/process_message_tests")
async def process_message_test(request: Request):
    try:
        payload = await request.json()
        logger.info("Payload recebido:\n%s", json.dumps(payload, indent=2, ensure_ascii=False))

        resultado = {
            "resposta_ia": request,
            "callback_result": payload
        }    

        logger.info(f"Processamento finalizado com sucesso para a interação {resultado}")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")
