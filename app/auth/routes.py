# app/auth/routes.py
from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.forms import LoginForm
from app.models import User

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para a home
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Futuramente, 'dashboard.index'

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Verifica se o usuário não existe OU se a senha está incorreta
        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválidos')
            return redirect(url_for('auth.login'))

        # Se deu tudo certo, faz o login
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('dashboard.index')) # Futuramente, 'dashboard.index'

    return render_template('auth/login.html', title='Entrar', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))