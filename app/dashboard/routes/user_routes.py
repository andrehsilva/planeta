# app/dashboard/routes/user_routes.py

# --- Imports Essenciais ---
from functools import wraps
from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user

# --- Imports do Projeto ---
from app.dashboard import bp               # O Blueprint do Dashboard
from app.extensions import db              # A instância do banco de dados
from app.models import User                # O modelo de dados de Usuário
from app.forms import (                    # Os formulários necessários
    AdminResetPasswordForm, 
    ChangePasswordForm
)

# --- Decorador de Permissão ---
# Como este decorador é usado apenas pelas rotas de usuário, ele fica bem aqui.
def admin_required(f):
    """Garante que apenas usuários com a role 'admin' possam acessar a rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Erro HTTP 403: Forbidden (Acesso Proibido)
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Administração de Usuários ---

@bp.route('/users')
@login_required
@admin_required
def list_users():
    """Lista todos os usuários cadastrados no sistema para o admin."""
    users = User.query.order_by(User.username).all()
    return render_template('dashboard/users.html', users=users, title="Gerenciar Usuários")

@bp.route('/users/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Aprova o cadastro de um novo usuário que está pendente."""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'O usuário {user.username} foi aprovado com sucesso!', 'success')
    return redirect(url_for('dashboard.list_users'))

@bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Alterna o papel de um usuário entre 'admin' e 'colaborador'."""
    user = User.query.get_or_404(user_id)
    
    # Regra de segurança para impedir que um admin remova o próprio acesso
    if user.id == current_user.id:
        flash('Você не pode alterar seu próprio status de administrador.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    if user.role == 'admin':
        user.role = 'colaborador'
        flash(f'{user.username} agora é um Colaborador.', 'info')
    else:
        user.role = 'admin'
        flash(f'{user.username} agora é um Administrador.', 'info')
        
    db.session.commit()
    return redirect(url_for('dashboard.list_users'))

@bp.route('/users/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Permite que um admin redefina a senha de qualquer usuário."""
    user = User.query.get_or_404(user_id)
    form = AdminResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(f'A senha de {user.username} foi redefinida com sucesso.', 'success')
        return redirect(url_for('dashboard.list_users'))
        
    return render_template('dashboard/reset_password.html', 
                           form=form, 
                           title=f"Redefinir Senha de {user.username}", 
                           user=user)

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Deleta um usuário do sistema."""
    user = User.query.get_or_404(user_id)

    # Regra de segurança CRÍTICA para impedir que um admin delete a si mesmo
    if user.id == current_user.id:
        flash('Você не pode excluir sua própria conta de administrador.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário "{user.username}" foi excluído com sucesso.', 'success')
    return redirect(url_for('dashboard.list_users'))

# --- Rota de Perfil do Usuário Logado ---

@bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Permite que o usuário logado altere sua própria senha."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Sua senha atual está incorreta.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!', 'success')
            return redirect(url_for('dashboard.index')) # Redireciona para a página inicial do dash
            
    return render_template('dashboard/change_password.html', form=form, title="Alterar Minha Senha")