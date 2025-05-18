from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.generativeservice import send_message_openai
from services.memorycacheservice import getKey, setKey
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessMessageRequest(BaseModel):
    interactionId: str
    numero_cliente: str
    message: Optional[str] = ""

@router.post("/process_message")
async def process_message(req: ProcessMessageRequest):
    try:
        logger.info(f"Requisição recebida: {req.model_dump()}")

        memory = getKey(req.numero_cliente)
        if memory is None:
            newMemory = req.message
        else:
            newMemory = memory + ";" + req.message
            
        redisResult = setKey(req.numero_cliente, newMemory)

        req.message = "Essa é a memória das outras mensagens enviadas pelo usuário separadas por ;: " + memory + ". Essa é a mensagem atual do usuário: " + req.message if memory else req.message

        openIaResponse = await send_message_openai(req.message)       

        logger.info(f"Processamento finalizado com sucesso para a interação {req.interactionId}")

        return {
            "resposta": 
            {
                "interactionId": req.interactionId,
                "resposta_ia": openIaResponse,
                "numero_cliente:": req.numero_cliente
            }      
        }

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

