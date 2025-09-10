# app/main/routes.py
from flask import render_template, request, abort, flash, redirect, url_for
from app.main import bp


from app.models import Post, Lead , HomePageContent, LandingPage

from app.extensions import db # Adicione db
from app.forms import LeadForm

import secrets
import os
from flask import current_app

@bp.route('/')
def index():
    latest_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(3).all()
    # Busca o conteúdo da homepage no banco de dados
    content = HomePageContent.query.first()

    if not content:
        # Se não houver conteúdo, cria um com os valores padrão para não quebrar o site
        content = HomePageContent()

    return render_template('public/index.html', latest_posts=latest_posts, content=content)


# --- ✅ NOVA ROTA PARA O ARQUIVO COMPLETO DO BLOG ---
@bp.route('/blog')
def blog_archive():
    """
    Rota para a página de arquivo do blog, com todas as postagens e paginação.
    """
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(is_published=True)\
                                 .order_by(Post.created_at.desc())\
                                 .paginate(page=page, per_page=9, error_out=False)

    return render_template('public/blog_archive.html', posts_pagination=posts_pagination)


@bp.route('/post/<slug>')
def post_detail(slug):
    """
    Exibe uma postagem completa com base no seu slug.
    """
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    gallery_filenames = [image.filename for image in post.gallery_images]
    return render_template('public/post_detail.html', post=post, gallery_filenames=gallery_filenames)


@bp.route('/lp/<slug>')
def view_landing_page(slug):
    """Renderiza a página de uma landing page publicada."""
    # Busca a primeira landing page publicada que corresponde ao slug
    lp = LandingPage.query.filter_by(slug=slug, is_published=True).first()
    
    if lp is None:
        # Se não encontrar, retorna um erro 404
        abort(404)
        
    return render_template('public/view_landing_page.html', lp=lp)


@bp.route('/politica-de-privacidade')
def privacy_policy():
    """Renderiza a página de Política de Privacidade."""
    return render_template('public/politica.html')

@bp.route('/contato', methods=['GET', 'POST'])
def contact():
    """Exibe e processa o formulário de contato/orçamento."""
    form = LeadForm()
    if form.validate_on_submit():
        new_lead = Lead(
            parent_name=form.parent_name.data,
            email=form.email.data,
            whatsapp=form.whatsapp.data,
            child_name=form.child_name.data,
            child_age=form.child_age.data,
            service_of_interest=form.service_of_interest.data,
            message=form.message.data
        )
        db.session.add(new_lead)
        db.session.commit()
        flash('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('public/contact.html', form=form)


@bp.app_context_processor
def inject_landing_pages():
    """
    Injeta uma lista de landing pages publicadas em todos os templates
    renderizados por este blueprint (o 'main').
    """
    try:
        # Busca no banco de dados todas as LPs que estão marcadas como publicadas
        published_landing_pages = LandingPage.query.filter_by(is_published=True).order_by(LandingPage.title).all()
        # Retorna um dicionário que será adicionado ao contexto do template
        return dict(nav_landing_pages=published_landing_pages)
    except Exception as e:
        # Em caso de erro (ex: banco de dados não disponível), retorna uma lista vazia
        return dict(nav_landing_pages=[])
    

def save_picture(form_picture, subfolder='uploads'):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', subfolder, picture_fn)
    form_picture.save(picture_path)
    return picture_fn


