# app/__init__.py
import os
from flask import Flask
from markupsafe import Markup
from commands import create_admin

# Importando as extensões que serão inicializadas
from .extensions import db, migrate, login_manager
from config import Config

def create_app(config_class=Config):
    """
    Fábrica de aplicativos (Application Factory).
    Cria e configura uma instância da aplicação Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # 1. CARREGAR A CONFIGURAÇÃO
    # Carrega a configuração padrão a partir da classe/arquivo config.py
    app.config.from_object(config_class)

    # CRÍTICO PARA PRODUÇÃO: Sobrescreve a URL do banco de dados se a variável
    # de ambiente 'DATABASE_URL' estiver definida (como no EasyPanel).
    if 'DATABASE_URL' in os.environ:
        db_url = os.environ['DATABASE_URL']
        # Garante a compatibilidade com o SQLAlchemy
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # 2. INICIALIZAR AS EXTENSÕES
    # Conecta as extensões à instância do nosso aplicativo
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from commands import create_admin
    app.cli.add_command(create_admin)

    # 3. REGISTRAR BLUEPRINTS E OUTROS COMPONENTES DO APP
    # O 'with app.app_context()' garante que tudo aqui dentro "enxergue" o app.
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

        # Registrar o filtro Jinja de forma mais moderna
        @app.template_filter('nl2br')
        def nl2br_filter(s):
            """Converte quebras de linha em tags <br>."""
            return Markup(s.replace('\n', '<br>')) if s else ''

        # Configurar o user_loader do Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            """Diz ao Flask-Login como carregar um usuário a partir de um ID."""
            return models.User.query.get(int(user_id))

    return app