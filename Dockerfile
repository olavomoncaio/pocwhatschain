# Usar imagem oficial do Python (com slim para reduzir tamanho)
FROM python:3.11-slim

# Instalar Redis e dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends redis-server && \
    rm -rf /var/lib/apt/lists/*

# Setar diretório de trabalho
WORKDIR /app

# Copiar arquivos (incluindo requirements.txt primeiro para cache eficiente)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install langchain-community langchain-core redis

# Copiar o restante dos arquivos
COPY . .

# Expor porta da sua API e do Redis (opcional)
EXPOSE 8000 6379

# Script para iniciar Redis + sua app
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]