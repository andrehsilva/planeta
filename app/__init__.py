# app/__init__.py
# --- VERSÃO CORRIGIDA DO WHITENOISE COM PERMISSÕES ---

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

    # --- CONFIGURAÇÃO DA PASTA DE UPLOADS COM PERMISSÕES ---
    with app.app_context():
        upload_path = app.config.get('UPLOAD_FOLDER')
        if upload_path:
            # Garante que a pasta existe com permissões corretas
            if not os.path.exists(upload_path):
                try:
                    os.makedirs(upload_path, mode=0o755)  # Permissões 755
                    print(f"✅ Pasta de uploads criada com sucesso em: {upload_path}")
                except Exception as e:
                    print(f"❌ Erro ao criar pasta de uploads em {upload_path}: {e}")
            else:
                # Se a pasta já existe, garante as permissões
                try:
                    os.chmod(upload_path, 0o755)
                    print(f"✅ Permissões da pasta verificadas: {upload_path}")
                except Exception as e:
                    print(f"⚠️  Erro ao ajustar permissões de {upload_path}: {e}")
            
            # Verifica se a pasta é gravável
            if not os.access(upload_path, os.W_OK):
                print(f"❌ ATENÇÃO: Pasta {upload_path} não é gravável!")
            else:
                print(f"✅ Pasta {upload_path} é gravável")

    # --- CONFIGURAÇÃO WHITENOISE OTIMIZADA ---
    if not app.debug:  # Só usar WhiteNoise em produção
        try:
            # Configuração WhiteNoise com cache reduzido para desenvolvimento
            app.wsgi_app = WhiteNoise(
                app.wsgi_app, 
                root='/app/media/', 
                prefix='media/',
                max_age=60,  # Cache de 1 minuto (ajustável)
                forever=False,  # Não usar cache permanente
                autorefresh=True  # Recarregar automaticamente
            )
            
            # Serve também a pasta static se necessário
            # app.wsgi_app.add_files('/app/static/', prefix='static/')
            
            print("✅ WhiteNoise configurado para servir /app/media/")
            
            # Verifica se a pasta media existe e é acessível
            if os.path.exists('/app/media'):
                media_files = len([f for f in os.listdir('/app/media') 
                                 if os.path.isfile(os.path.join('/app/media', f))])
                print(f"📁 WhiteNoise servindo {media_files} arquivos de /app/media/")
            else:
                print("❌ ATENÇÃO: Pasta /app/media/ não encontrada!")
                
        except Exception as e:
            print(f"❌ Erro ao configurar WhiteNoise: {e}")
            # Fallback: usar rota Flask para servir arquivos
            @app.route('/media/<path:filename>')
            def serve_media_fallback(filename):
                from flask import send_from_directory
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            print("✅ Fallback Flask configurado para servir arquivos media")

    return app