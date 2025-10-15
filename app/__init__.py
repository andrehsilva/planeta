import os
from flask import Flask
from markupsafe import Markup
from . import commands
from whitenoise import WhiteNoise

# Importando as extensões que serão inicializadas
from .extensions import db, migrate, login_manager
# --- ALTERADO ---
# Importa o dicionário de configurações em vez de uma única classe
from config import config_by_name

def create_app(config_name=None):
    """
    Fábrica de aplicativos (Application Factory).
    Cria e configura uma instância da aplicação Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- LÓGICA DE CONFIGURAÇÃO MELHORADA ---
    # 1. Determina qual configuração carregar (development ou production)
    #    com base na variável de ambiente FLASK_ENV.
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    # 2. Carrega a configuração do objeto correspondente.
    app.config.from_object(config_by_name[config_name])

    # Configurações adicionais
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    # --- REMOVIDO ---
    # A lógica de sobrescrever o DATABASE_URL foi movida para o arquivo
    # config.py, dentro da classe ProductionConfig, tornando este
    # arquivo mais limpo e a configuração mais centralizada.

    # INICIALIZAÇÃO DAS EXTENSÕES
    # Conecta as extensões à instância do nosso aplicativo
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Registra os comandos customizados (ex: flask create-admin)
    commands.register_commands(app)

    # REGISTRO DE BLUEPRINTS E OUTROS COMPONENTES DO APP
    with app.app_context():
        # Importar os modelos aqui garante que eles sejam reconhecidos pelo Flask-Migrate
        from . import models

        # Registrar os Blueprints (módulos da nossa aplicação)
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
    # Este código agora funciona para ambos os ambientes, pois app.config['UPLOAD_FOLDER']
    # terá o valor correto (relativo ou absoluto) dependendo do FLASK_ENV.
    with app.app_context():
        upload_path = app.config.get('UPLOAD_FOLDER')
        if upload_path and not os.path.exists(upload_path):
            try:
                os.makedirs(upload_path)
                print(f"Pasta de uploads criada com sucesso em: {upload_path}")
            except Exception as e:
                print(f"Erro ao criar pasta de uploads em {upload_path}: {e}")

    app.wsgi_app = WhiteNoise(app.wsgi_app, root='app/static/') # <--- 2. ADICIONE ESTA LINHA


    return app
