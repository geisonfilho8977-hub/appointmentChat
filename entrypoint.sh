#!/bin/bash
set -e

# Gera o arquivo .env do backend automaticamente a partir do ambiente do container
cat << ENVEOF > /app/.env
DATABASE_URL=${DATABASE_URL}
OPENAI_API_KEY=${OPENAI_API_KEY}
ADMIN_SECRET_KEY=${ADMIN_SECRET_KEY}
ENVEOF

echo "✅ Arquivo /app/.env gerado automaticamente no container do backend!"

echo "⏳ Aguardando banco de dados PostgreSQL inicializar..."
python -c "
import time, os
from Infrastructure.Database.Connection import get_connection
for i in range(30):
    try:
        with get_connection() as conn:
            print('✅ PostgreSQL pronto e conectado!')
            break
    except Exception as e:
        print(f'Tentativa {i+1}/30: Aguardando PostgreSQL... ({e})')
        time.sleep(2)
"

echo "🚀 Iniciando Galeno Backend na porta 8000..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
