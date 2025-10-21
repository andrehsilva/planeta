# Dockerfile

# Passo 1: Imagem Base
FROM python:3.11-slim-bookworm

# Passo 2: Variáveis de Ambiente
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Passo 3: Diretório de Trabalho
WORKDIR /app

# Passo 4: Instalar Dependências do Sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Passo 5: Instalar Dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CORREÇÃO PRINCIPAL ---
# Passo 6: Copiar explicitamente os ficheiros e pastas da aplicação.
# Isto garante que a pasta 'static' (com 'images') seja incluída.
# Copia todo o app, incluindo a pasta static
COPY app ./app
COPY config.py .
COPY migrations ./migrations

# --- CORREÇÃO APLICADA AQUI ---
# Cria a pasta de MÍDIA (para o volume de uploads) e ajusta permissões
RUN mkdir -p /app/media && chmod -R 777 /app/media

COPY pyproject.toml .
# Adicione outras pastas ou ficheiros de topo se necessário (ex: tests, etc.)

# Passo 7: Expor a Porta
EXPOSE $PORT

# Passo 8: Comando de Execução
CMD gunicorn --bind 0.0.0.0:$PORT "app:create_app()"

