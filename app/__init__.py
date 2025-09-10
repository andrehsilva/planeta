# app/__init__.py
from flask import Flask
from config import Config  # Usaremos um arquivo de configuração separado
from app.extensions import db, migrate, login
from app.models import User
from app import models 
from markupsafe import Markup 

def nl2br_filter(s):
    """Converte quebras de linha em tags <br>."""
    if s:
        return Markup(s.replace('\n', '<br>\n'))
    return ''

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa as extensões com o app

    app.jinja_env.filters['nl2br'] = nl2br_filter
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
  

    # Registra os Blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    # Essencial: Esta função diz ao Flask-Login como encontrar um usuário a partir do ID
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app