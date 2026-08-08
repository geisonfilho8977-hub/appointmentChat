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

# Verifica se o banco de dados já possui as tabelas inicializadas
TABLE_EXISTS=$(python -c "
from Infrastructure.Database.Connection import get_connection
try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'patients');\")
            print(cur.fetchone()[0])
except Exception:
    print('False')
")

if [ "$TABLE_EXISTS" != "True" ]; then
    echo "📦 Banco de dados novo detectado! Inicializando esquemas e dados..."
    DB_HOST=$(python -c "from urllib.parse import urlparse; import os; u=urlparse(os.getenv('DATABASE_URL','')); print(u.hostname or 'postgres')")
    DB_USER=$(python -c "from urllib.parse import urlparse; import os; u=urlparse(os.getenv('DATABASE_URL','')); print(u.username or 'galeno_user')")
    DB_PASS=$(python -c "from urllib.parse import urlparse; import os; u=urlparse(os.getenv('DATABASE_URL','')); print(u.password or 'galeno_pass')")
    DB_NAME=$(python -c "from urllib.parse import urlparse; import os; u=urlparse(os.getenv('DATABASE_URL','')); print(u.path.lstrip('/') or 'galeno_db')")

    if [ -f "/app/sql/users.sql" ]; then
        echo "Importando users.sql..."
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /app/sql/users.sql
    fi
    if [ -f "/app/sql/appointment.sql.gz" ]; then
        echo "Importando dados de pacientes/sintomas (appointment.sql.gz)..."
        zcat /app/sql/appointment.sql.gz | PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME
    elif [ -f "/app/sql/appointment.sql" ]; then
        echo "Importando appointment.sql..."
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /app/sql/appointment.sql
    fi
    echo "✅ Banco de dados inicializado com sucesso!"
fi

echo "🚀 Iniciando Galeno Backend na porta 8000..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
