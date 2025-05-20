from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional
from services.generativeservice import send_message_openai
from services.memorycacheservice import getKey, setKey
from services.whatsappservice import send_callback_whatsapp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ZapiWebhookData(BaseModel):
    type: str
    from_: str = Field(alias="from")
    fromName: Optional[str]
    message: Optional[str]
    messageId: Optional[str]
    timestamp: Optional[int]
  
class ZapiWebhookModel(BaseModel):
    event: str
    instanceId: str
    timestamp: int
    data: ZapiWebhookData

@router.post("/process_message")
async def process_message(request: ZapiWebhookModel):
    try:
        logger.info(f"Requisição recebida: {request}")

        openIaResponse = await send_message_openai(request.data.message) 
        callbackResult = await send_callback_whatsapp(openIaResponse, request.data.from_)      

        resultado = {
                "resposta_ia": openIaResponse,
                "numero_cliente:": request.data.from_,
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

