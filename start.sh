#!/bin/bash
# Inicia o Redis em segundo plano
redis-server --daemonize yes

# Inicia sua aplicação Python
uvicorn main:app --host 0.0.0.0 --port 8000