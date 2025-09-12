# commands.py
import click
from flask.cli import with_appcontext
from sqlalchemy import text  # Importe 'text' para executar SQL puro
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
    Exemplo: flask create_admin nome_admin admin@email.com senha_segura
    """
    if User.query.filter_by(username=username).first():
        click.echo(f"Erro: Usuário '{username}' já existe.")
        return
    if User.query.filter_by(email=email).first():
        click.echo(f"Erro: Email '{email}' já está em uso.")
        return

    admin_user = User(username=username, email=email, role='admin')
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    click.echo(f"Administrador '{username}' criado com sucesso!")


# ✅ NOVO COMANDO ADICIONADO AQUI
@click.command(name='db-reset-history')
@with_appcontext
def db_reset_history():
    """Apaga a tabela alembic_version para resetar o histórico de migrações."""
    try:
        db.session.execute(text('DROP TABLE IF EXISTS alembic_version;'))
        db.session.commit()
        click.echo("Histórico de migração (tabela alembic_version) removido com sucesso.")
        click.echo("Agora você pode rodar 'flask db upgrade' para criar o banco do zero.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Erro ao remover o histórico de migração: {e}")


# ✅ FUNÇÃO PARA REGISTRAR TODOS OS COMANDOS
def register_commands(app):
    """Registra os comandos CLI com a aplicação Flask."""
    app.cli.add_command(create_admin)
    app.cli.add_command(db_reset_history) # Adiciona o novo comando