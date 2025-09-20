# app/dashboard/__init__.py

from flask import Blueprint

bp = Blueprint('dashboard', __name__, template_folder='templates')

# Importa todos os novos módulos de rotas para registrá-los no blueprint
from app.dashboard.routes import (
    homepage_routes, 
    user_routes,
    client_routes,
    post_routes,
    leads_routes,
    landingpage_routes,
    popup_routes,
    general_routes
)