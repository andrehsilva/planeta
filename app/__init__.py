# app/__init__.py
# --- VERSÃO COM A CORREÇÃO DO WHITENOISE ---

import os
from flask import Flask
from markupsafe import Markup
from . import commands
from whitenoise import WhiteNoise

# Importando as extensões
from .extensions import db, migrate, login_manager
from config import config_by_name

def create_app(config_name=None):
    """
    Fábrica de aplicativos (Application Factory).
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuração ---
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config_by_name[config_name])
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    # --- Inicialização das Extensões ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Registra os comandos
    commands.register_commands(app)

    # --- Blueprints e Componentes ---
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

    # Cria a pasta de uploads se não existir
    with app.app_context():
        upload_path = app.config.get('UPLOAD_FOLDER')
        if upload_path and not os.path.exists(upload_path):
            try:
                os.makedirs(upload_path)
                print(f"Pasta de uploads criada com sucesso em: {upload_path}")
            except Exception as e:
                print(f"Erro ao criar pasta de uploads em {upload_path}: {e}")

    whitenoise_instance = WhiteNoise(app.wsgi_app, root='/app/media/', prefix='media/')
    app.wsgi_app = whitenoise_instance

    return app
#

