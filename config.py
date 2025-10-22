""" # config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# --- CLASSE BASE ---
# Contém as configurações que são comuns a todos os ambientes
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Definimos um valor padrão, mas será sobrescrito
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    UPLOAD_FOLDER = None # Será definido nas classes filhas

# --- CONFIGURAÇÃO DE DESENVOLVIMENTO ---
class DevelopmentConfig(Config):
    DEBUG = True
    # Usa o caminho relativo para o banco de dados SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    # Usa o caminho relativo para a pasta de uploads, que funciona localmente
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')

# --- CONFIGURAÇÃO DE PRODUÇÃO ---
class ProductionConfig(Config):
    DEBUG = False
    # O DATABASE_URL será pego da variável de ambiente no EasyPanel
    # Usa o caminho absoluto para a pasta de uploads, que funciona no Docker
    #UPLOAD_FOLDER = '/app/static/uploads'
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')


# Dicionário para facilitar a seleção da configuração
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} """


# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# --- CLASSE BASE ---
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    UPLOAD_FOLDER = '/app/media'

# --- CONFIGURAÇÃO DE DESENVOLVIMENTO ---
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    # Para desenvolvimento, podemos usar uma subpasta em 'static'
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')

# --- CONFIGURAÇÃO DE PRODUÇÃO ---
class ProductionConfig(Config):
    DEBUG = False
    # ESTA É A MUDANÇA CRÍTICA:
    # A pasta de uploads agora é /app/media, separada da pasta /app/static.
    #UPLOAD_FOLDER = '/app/static/uploads'
    UPLOAD_FOLDER = '/app/media' # <--- MUDANÇA

# Dicionário para facilitar a seleção
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
