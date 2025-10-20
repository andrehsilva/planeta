# app/__init__.py
# --- VERSÃO FINAL E CORRIGIDA ---

import os
from flask import Flask
from markupsafe import Markup
from . import commands
from whitenoise import WhiteNoise  # 1. Importar o WhiteNoise

# Importando as extensões que serão inicializadas
from .extensions import db, migrate, login_manager
from config import config_by_name

def create_app(config_name=None):
    """
    Fábrica de aplicativos (Application Factory).
    Cria e configura uma instância da aplicação Flask.
    """
    
    # 2. ESTA É A CORREÇÃO PRINCIPAL E DEFINITIVA:
    # Vamos calcular o caminho absoluto para a pasta /app
    # O basedir será /app
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Agora dizemos ao Flask para usar o caminho absoluto /app/static
    # como sua pasta de arquivos estáticos.
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder=os.path.join(basedir, 'static'),
                static_url_path='/static')

    # --- LÓGICA DE CONFIGURAÇÃO ---
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config_by_name[config_name])
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    # --- INICIALIZAÇÃO DAS EXTENSÕES ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Registra os comandos customizados
    commands.register_commands(app)

    # --- REGISTRO DE BLUEPRINTS E OUTROS COMPONENTES ---
    with app.app_context():
        from . import models

        from .main import bp as main_bp
        app.register_blueprint(main_bp)

        from .auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from .dashboard import bp as dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

        @app.template_filter('nl2br')
        def nl2br_filter(s):
            return Markup(s.replace('\n', '<br>')) if s else ''

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

    # CRIA A PASTA DE UPLOADS (Ainda usa a config absoluta)
    with app.app_context():
        upload_path = app.config.get('UPLOAD_FOLDER')
        if upload_path and not os.path.exists(upload_path):
            try:
                os.makedirs(upload_path)
                print(f"Pasta de uploads criada com sucesso em: {upload_path}")
            except Exception as e:
                print(f"Erro ao criar pasta de uploads em {upload_path}: {e}")

    # 3. CONFIGURAÇÃO FINAL DO WHITENOISE:
    # Esta linha simples faz o WhiteNoise ler automaticamente
    # a configuração 'static_folder' correta que definimos acima.
    app.wsgi_app = WhiteNoise(app.wsgi_app)
    
    return app