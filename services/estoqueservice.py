import json
from typing import List, Dict
from sqlalchemy.orm import Session
import logging
from models.models import Empresa 
from services.memorycacheasyncservice import set_key

logger = logging.getLogger(__name__)

class EstoqueService:
    def __init__(self, db: Session):
        self.db = db

    def criar_estoque(self, empresa_id: str, itens: List[Dict]) -> bool:
        try:
            if self.db.query(Empresa).filter(Empresa.id == empresa_id).first():
                logger.warning(f"Empresa {empresa_id} já possui estoque registrado. É necessário atualizar o estoque existente.")
                return False

            novo_estoque = Empresa(id=empresa_id, estoque=itens)
            self.db.add(novo_estoque)
            self.db.commit()

            json_itens = json.dumps(itens)
            cacheKey = f"estoque:{empresa_id}"
            set_key(cacheKey, json_itens)

            return True

        except Exception as e:
            logger.error(f"Erro ao criar estoque: {e}")
            self.db.rollback()
            return False

    def atualizar_estoque(self, empresa_id: int, novos_itens: List[Dict]) -> bool:
        try:
            logger.info(f"Iniciando update de estoque.")

            empresa = self.db.query(Empresa).filter(Empresa.id == empresa_id).first()
            if not empresa:
                logger.info(f"Empresa {empresa_id} não encontrada. É necessário criar o estoque primeiro.")
                return False

            logger.info(f"Aplicando update de estoque.")
            empresa.estoque = novos_itens
            self.db.commit()

            json_itens = json.dumps(novos_itens)
            cacheKey = f"estoque:{empresa_id}"
            set_key(cacheKey, json_itens)
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar estoque: {e}")
            self.db.rollback()
            return False
        
    def obter_estoque(self, empresa_id: str) -> List[Dict]:
        try:
            logger.info(f"Obtendo estoque para a empresa {empresa_id}.")
            empresa = self.db.query(Empresa).filter(Empresa.id == empresa_id).first()
            if not empresa:
                logger.warning(f"Empresa {empresa_id} não encontrada.")
                return []

            estoqueKey = f"estoque:{empresa_id}"    
            estoque_json = json.dumps(empresa.estoque)
            
            set_key(estoqueKey, estoque_json)

            return empresa.estoque

        except Exception as e:
            logger.error(f"Erro ao obter estoque: {e}")
            return []