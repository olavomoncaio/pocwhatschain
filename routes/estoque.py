from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging
from sqlalchemy.orm import Session
from services.estoqueservice import EstoqueService
from models.models import get_db 

logger = logging.getLogger(__name__)

router = APIRouter()

class ItemEstoque(BaseModel):
    nome: str
    preco: str
    estoque: str
    descricao: str
    codigo: str
    permite_fracionamento: bool 

    def to_dict(self):
        return {
            "nome": self.nome,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "preco": str(self.preco),  # Converte Decimal para string se necessário
            "estoque": self.estoque,
            "permite_fracionamento": self.permite_fracionamento
        }

class CriarEstoquePayload(BaseModel):
    empresa_id: str
    itens: List[ItemEstoque]

@router.post("/", status_code=201)
async def criar_estoque(
    payload: CriarEstoquePayload,
    db: Session = Depends(get_db)
):
    service = EstoqueService(db)
    success = service.criar_estoque(payload.empresa_id, [item.to_dict() for item in payload.itens])
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Empresa {payload.empresa_id} já possui estoque ou dados inválidos"
        )
    return {"message": "Estoque criado com sucesso"}

@router.put("/{empresa_id}")
async def atualizar_estoque(
    payload: CriarEstoquePayload,
    db: Session = Depends(get_db)
):
    service = EstoqueService(db)

    itens_serializados = [item.to_dict() for item in payload.itens]
    success = service.atualizar_estoque(payload.empresa_id, itens_serializados)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Empresa {payload.empresa_id} não encontrada"
        )
    return {"message": "Estoque atualizado com sucesso"}

@router.get("/{empresa_id}")
async def obter_estoque(
    empresa_id: str,
    db: Session = Depends(get_db)
):
    service = EstoqueService(db)
    estoque = service.obter_estoque(empresa_id)
    
    if not estoque:
        raise HTTPException(
            status_code=404,
            detail=f"Estoque não encontrado para a empresa {empresa_id}"
        )
    return estoque