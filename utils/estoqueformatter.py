import json
from typing import Union
import logging

logger = logging.getLogger(__name__)

@staticmethod
def format_estoque(estoque_json: Union[str, list, dict]) -> str:
    try:
        if isinstance(estoque_json, str):
            estoque = json.loads(estoque_json)
        elif isinstance(estoque_json, bytes):
            estoque = json.loads(estoque_json.decode('utf-8'))
        else:
            estoque = estoque_json

        textos = []
        for produto in estoque:
            textos.append(
                f"- {produto['nome']}\n"
                f"  Código: {produto['codigo']}\n"
                f"  Descrição: {produto['descricao']}\n"
                f"  Preço: {produto['preco']}\n"
                f"  Estoque: {produto['estoque']}\n"
                f"  Fracionamento: {'sim' if produto.get('permite_fracionamento', False) else 'não'}"
            )

        return "\n\n".join(textos)
        
    except Exception as e:
        logger.error(f"Erro ao formatar estoque: {e}")
        return "Não possui itens em estoque"    
    

