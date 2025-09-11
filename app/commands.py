# commands.py
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User

@click.command(name='create_admin')
@with_appcontext
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin(username, email, password):
    """
    Cria um novo usuário administrador.
    Exemplo de uso: python3 -m flask create_admin nome_admin admin@email.com senha_segura
    """
    if User.query.filter_by(username=username).first():
        click.echo(f"Erro: Usuário '{username}' já existe.")
        return
    if User.query.filter_by(email=email).first():
        click.echo(f"Erro: Email '{email}' já está em uso.")
        return

    # Cria um novo usuário com a role 'admin'
    admin_user = User(username=username, email=email, role='admin')
    # Define a senha usando o método seguro que gera o hash
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    click.echo(f"Administrador '{username}' criado com sucesso!")