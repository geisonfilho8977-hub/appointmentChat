FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema e postgresql-client para automação de scripts SQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte da aplicação e pasta SQL
COPY . .

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
