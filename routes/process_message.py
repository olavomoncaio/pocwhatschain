from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.generativeservice import chainWelcomeBack, classify_client_response, chainPlaceAnOrder, general_response
from services.memorycacheservice import verifyPreviousConversations, clear_memory
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessMessageRequest(BaseModel):
    interactionId: str
    numero_cliente: str
    nome_cliente: str
    message: Optional[str] = ""

@router.post("/process_message")
async def process_message(req: ProcessMessageRequest):
    try:
        resposta = ""
        logger.info(f"Requisição recebida: {req.model_dump()}")

        has_previous_conversation = verifyPreviousConversations(req.numero_cliente)

        if(has_previous_conversation):
            welcome_message = chainWelcomeBack(req.client_id).invoke({"input": req.nome_cliente})
            user_input = input(welcome_message["text"] + "\n>> ")
            
            # Classifica a resposta do cliente
            classification = classify_client_response(user_input)
            
            if classification in ['não', 'nao', 'n']:
                clear_memory()
                print("OK, vamos iniciar um novo atendimento. Como posso ajudar?")

            elif classification in ['fechar']:
                placeanorder_message = chainPlaceAnOrder.invoke({"input": req.nome_cliente})
                print(placeanorder_message["text"] + "\n>> ")

            else:
                general_response(user_input)
        else: 
            general_response(user_input)      

        logger.info(f"Processamento finalizado com sucesso para o cliente {req.numero_cliente}")

        return {
            "resposta": 
            {
                "interactionId": req.interactionId,
                "resposta_ia": resposta,
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

