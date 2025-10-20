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

# Passo 6: Copiar o Código da Aplicação
# ESTA É A CORREÇÃO CRÍTICA:
# Copiamos a pasta 'app' e os arquivos de configuração PRIMEIRO.
COPY app ./app
COPY migrations ./migrations
COPY config.py .
COPY app.db . 
# ... adicione outros arquivos da raiz do seu projeto aqui se necessário

# DEPOIS, copiamos a pasta 'static'. Isso garante que ela não seja
# sobrescrita pela montagem do volume que acontece depois.
COPY static ./static

# Passo 7: Expor a Porta
EXPOSE $PORT

# Passo 8: Comando de Execução
CMD gunicorn --bind 0.0.0.0:$PORT "app:create_app()"
