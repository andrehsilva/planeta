# Dockerfile

# Passo 1: Imagem Base
# Começamos com uma imagem oficial do Python 3.11, versão 'slim', que é leve.
# 'bookworm' é a versão estável mais recente do Debian.
FROM python:3.11-slim-bookworm

# Passo 2: Variáveis de Ambiente
# Garante que os logs do Python apareçam imediatamente, o que é ótimo para debug.
ENV PYTHONUNBUFFERED=1
# Define a porta padrão que o container vai usar. O EasyPanel pode sobrescrever isso.
ENV PORT=8080

# Passo 3: Diretório de Trabalho
# Cria e define o diretório de trabalho dentro do container.
WORKDIR /app

# Passo 4: Instalar Dependências do Sistema
# O passo crucial que substitui o 'aptPkgs' do nixpacks.toml.
# Instala as ferramentas necessárias para compilar pacotes como o numpy.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Passo 5: Instalar Dependências do Python
# Copia APENAS o requirements.txt primeiro para aproveitar o cache do Docker.
# Se este arquivo não mudar, o Docker não reinstalará tudo a cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Passo 6: Copiar o Código da Aplicação
# Com as dependências já instaladas, agora copiamos o resto do nosso código.
COPY . .

# Passo 7: Expor a Porta
# Informa ao Docker que o container escutará na porta definida pela variável $PORT.
# É uma boa prática de documentação.
EXPOSE $PORT

# Passo 8: Comando de Execução
# O comando que será executado quando o container iniciar.
# Inicia o servidor Gunicorn, apontando para a nossa application factory.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:create_app()"]