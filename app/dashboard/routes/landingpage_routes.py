# app/dashboard/routes/landingpage_routes.py

# --- Imports Essenciais ---
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from werkzeug.datastructures import FileStorage
from slugify import slugify

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import LandingPage
from app.forms import LandingPageForm
# --- IMPORTAÇÃO CENTRALIZADA DAS FUNÇÕES DE UPLOAD ---
from app.utils import save_picture, delete_file_from_uploads


# --- Rotas de Gerenciamento de Landing Pages ---

@bp.route('/landingpages')
@login_required
def list_landing_pages():
    """Lista todas as Landing Pages criadas com paginação."""
    page = request.args.get('page', 1, type=int)
    landing_pages_pagination = LandingPage.query.order_by(LandingPage.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('dashboard/list_landing_pages.html',
                           landing_pages_pagination=landing_pages_pagination,
                           title="Landing Pages")

@bp.route('/landingpages/new', methods=['GET', 'POST'])
@login_required
def add_landing_page():
    """Formulário para criar uma nova Landing Page."""
    form = LandingPageForm()
    if form.validate_on_submit():
        new_lp = LandingPage(
            title=form.title.data,
            slug=slugify(form.title.data),
            is_published=form.is_published.data,
            hero_title=form.hero_title.data,
            hero_subtitle=form.hero_subtitle.data,
            hero_cta_text=form.hero_cta_text.data,
            hero_cta_link=form.hero_cta_link.data,
            content_title=form.content_title.data,
            content_body=form.content_body.data
        )

        if isinstance(form.hero_image.data, FileStorage):
            new_lp.hero_image = save_picture(form.hero_image.data)

        if isinstance(form.content_image.data, FileStorage):
            new_lp.content_image = save_picture(form.content_image.data)

        db.session.add(new_lp)
        db.session.commit()
        flash('Landing Page criada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_landing_pages'))
        
    return render_template('dashboard/manage_landing_page.html', form=form, title='Nova Landing Page')

@bp.route('/landingpages/edit/<int:lp_id>', methods=['GET', 'POST'])
@login_required
def edit_landing_page(lp_id):
    """Formulário para editar uma Landing Page existente."""
    lp = LandingPage.query.get_or_404(lp_id)
    form = LandingPageForm(obj=lp)
    if form.validate_on_submit():
        # Atualiza os campos de texto e booleanos
        lp.title = form.title.data
        lp.slug = slugify(form.title.data)
        lp.is_published = form.is_published.data
        lp.hero_title = form.hero_title.data
        lp.hero_subtitle = form.hero_subtitle.data
        lp.hero_cta_text = form.hero_cta_text.data
        lp.hero_cta_link = form.hero_cta_link.data
        lp.content_title = form.content_title.data
        lp.content_body = form.content_body.data

        # Atualiza as imagens, removendo a antiga se uma nova for enviada
        if isinstance(form.hero_image.data, FileStorage):
            delete_file_from_uploads(lp.hero_image)
            lp.hero_image = save_picture(form.hero_image.data)
            
        if isinstance(form.content_image.data, FileStorage):
            delete_file_from_uploads(lp.content_image)
            lp.content_image = save_picture(form.content_image.data)

        db.session.commit()
        flash('Landing Page atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_landing_pages'))
        
    return render_template('dashboard/manage_landing_page.html', form=form, title='Editar Landing Page', landing_page=lp)

@bp.route('/landingpages/delete/<int:lp_id>', methods=['POST'])
@login_required
def delete_landing_page(lp_id):
    """Rota para excluir uma Landing Page e suas imagens associadas."""
    lp = LandingPage.query.get_or_404(lp_id)
    
    # Remove as imagens associadas do servidor antes de deletar o registro
    delete_file_from_uploads(lp.hero_image)
    delete_file_from_uploads(lp.content_image)
    
    db.session.delete(lp)
    db.session.commit()
    flash('Landing Page excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_landing_pages'))
