import json
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional
from services.generativeservice import send_message_openai
from services.memorycacheservice import getKey, setKey
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
async def process_message(request: ReceivedCallbackModel):
    try:
        logger.info("Payload recebido:", request.model_dump())

        openIaResponse = await send_message_openai(request.text.message) 
        callbackResult = await send_callback_whatsapp(openIaResponse, request.phone)      

        resultado = {
                "resposta_ia": request,
                "callback_result": callbackResult
            }    

        logger.info(f"Processamento finalizado com sucesso para a interação {resultado}")

        return resultado     

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")
    
@router.post("/getKey")
async def getKeyCache(key: str):
    try:
        logger.info(f"Requisição recebida getKey: {key}")

        redisResult = getKey(key)
    
        logger.info(f"Processamento finalizado com sucesso para salvar chave")

        return {
            "resultado": redisResult
        }

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")
    
@router.post("/setKey")
async def setKeyCache(key: str, value: str):
    try:
        logger.info(f"Requisição recebida setKey: {key}")

        redisResult = setKey(key, value)
    
        logger.info(f"Processamento finalizado setar chave")

        return {
            "resultado": redisResult
        }

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise BaseException(status_code=500, detail=f"Ocorreu um erro ao processar a mensagem {str(e)}")

