# app/dashboard/routes/popup_routes.py

# --- Imports Essenciais ---
from flask import render_template, flash, redirect, url_for
from flask_login import login_required

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import Popup
from app.forms import PopupForm
# --- IMPORTAÇÃO CENTRALIZADA DAS FUNÇÕES DE UPLOAD ---
from app.utils import save_picture, delete_file_from_uploads


# --- Rotas de Gerenciamento de Popups ---

@bp.route('/popups')
@login_required
def list_popups():
    """Lista todos os popups criados."""
    popups = Popup.query.order_by(Popup.created_at.desc()).all()
    return render_template('dashboard/popups.html', popups=popups, title="Gerenciar Popups")

@bp.route('/popups/new', methods=['GET', 'POST'])
@login_required
def add_popup():
    """Adiciona um novo popup."""
    form = PopupForm()
    if form.validate_on_submit():
        if not form.image.data:
            flash('O campo de imagem é obrigatório para um novo popup.', 'danger')
            return render_template('dashboard/manage_popup.html', form=form, title="Novo Popup")

        # Se este popup for ativado, desativa todos os outros primeiro
        if form.is_active.data:
            Popup.query.update({Popup.is_active: False})

        filename = save_picture(form.image.data)
        
        new_popup = Popup(
            title=form.title.data,
            image_filename=filename,
            target_url=form.target_url.data,
            is_active=form.is_active.data,
            display_mode=form.display_mode.data 
        )
        db.session.add(new_popup)
        db.session.commit()
        flash('Popup criado com sucesso!', 'success')
        return redirect(url_for('dashboard.list_popups'))
        
    return render_template('dashboard/manage_popup.html', form=form, title="Novo Popup")

@bp.route('/popups/edit/<int:popup_id>', methods=['GET', 'POST'])
@login_required
def edit_popup(popup_id):
    """Edita um popup existente."""
    popup = Popup.query.get_or_404(popup_id)
    form = PopupForm(obj=popup)

    if form.validate_on_submit():
        # Se este popup for ativado, desativa todos os outros
        if form.is_active.data:
            Popup.query.filter(Popup.id != popup_id).update({Popup.is_active: False})

        # Se uma nova imagem foi enviada, deleta a antiga e salva a nova
        if form.image.data:
            delete_file_from_uploads(popup.image_filename)
            popup.image_filename = save_picture(form.image.data)

        popup.title = form.title.data
        popup.target_url = form.target_url.data
        popup.is_active = form.is_active.data
        popup.display_mode = form.display_mode.data
        
        db.session.commit()
        flash('Popup atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard.list_popups'))

    return render_template('dashboard/manage_popup.html', form=form, title="Editar Popup", popup=popup)

@bp.route('/popups/delete/<int:popup_id>', methods=['POST'])
@login_required
def delete_popup(popup_id):
    """Deleta um popup e sua imagem associada."""
    popup = Popup.query.get_or_404(popup_id)
    
    # Deleta o arquivo de imagem do servidor antes de remover o registro do BD
    delete_file_from_uploads(popup.image_filename)
    
    db.session.delete(popup)
    db.session.commit()
    flash('Popup deletado com sucesso!', 'success')
    return redirect(url_for('dashboard.list_popups'))
