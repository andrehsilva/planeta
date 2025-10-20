import os
from flask import Flask
from markupsafe import Markup
from . import commands
from whitenoise import WhiteNoise  # 1. Importe o WhiteNoise

# Importando as extensões que serão inicializadas
from .extensions import db, migrate, login_manager
from config import config_by_name

def create_app(config_name=None):
    """
    Fábrica de aplicativos (Application Factory).
    Cria e configura uma instância da aplicação Flask.
    """
    
    # 2. ESTA É A CORREÇÃO PRINCIPAL PARA O FLASK:
    # Diz ao Flask que a pasta 'static' está um nível ACIMA
    # deste arquivo (ou seja, em /app/static/ e não em /app/app/static/)
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='../static',
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

        # Registrar o filtro Jinja
        @app.template_filter('nl2br')
        def nl2br_filter(s):
            """Converte quebras de linha em tags <br>."""
            return Markup(s.replace('\n', '<br>')) if s else ''

        # Configurar o user_loader do Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            """Diz ao Flask-Login como carregar um usuário a partir de um ID."""
            return models.User.query.get(int(user_id))

    # CRIA A PASTA DE UPLOADS SE ELA NÃO EXISTIR
    with app.app_context():
        upload_path = app.config.get('UPLOAD_FOLDER')
        if upload_path and not os.path.exists(upload_path):
            try:
                os.makedirs(upload_path)
                print(f"Pasta de uploads criada com sucesso em: {upload_path}")
            except Exception as e:
                print(f"Erro ao criar pasta de uploads em {upload_path}: {e}")

    # 3. ESTA É A CORREÇÃO DO WHITENOISE:
    # Esta linha simples faz o WhiteNoise ler automaticamente
    # a configuração correta que definimos acima no Flask.
    app.wsgi_app = WhiteNoise(app.wsgi_app)
    
    return app