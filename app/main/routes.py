# app/main/routes.py

# --- Imports Essenciais ---
from flask import render_template, request, abort, flash, redirect, url_for

# --- Imports do Projeto ---
from app.main import bp
from app.models import Post, Lead , HomePageContent, LandingPage, Settings
from app.extensions import db
from app.forms import LeadForm

# --- Rotas Públicas ---

@bp.route('/')
def index():
    """Renderiza a página inicial do site."""
    content = HomePageContent.query.first()

    if not content:
        content = HomePageContent()
        db.session.add(content)
        db.session.commit()

    latest_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(3).all()
    ordered_sections = content.section_order.split(',') if content.section_order else []

    return render_template(
        'public/index.html',
        content=content,
        latest_posts=latest_posts,
        ordered_sections=ordered_sections
    )

@bp.route('/blog')
def blog_archive():
    """Renderiza a página de arquivo do blog com todas as postagens."""
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(is_published=True)\
                                 .order_by(Post.created_at.desc())\
                                 .paginate(page=page, per_page=9, error_out=False)
    return render_template('public/blog_archive.html', posts_pagination=posts_pagination)

@bp.route('/post/<slug>')
def post_detail(slug):
    """Exibe uma postagem completa com base no seu slug."""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    gallery_filenames = [image.filename for image in post.gallery_images]
    return render_template('public/post_detail.html', post=post, gallery_filenames=gallery_filenames)

@bp.route('/lp/<slug>')
def view_landing_page(slug):
    """Renderiza a página de uma landing page publicada."""
    lp = LandingPage.query.filter_by(slug=slug, is_published=True).first_or_404()
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

# --- Processador de Contexto ---

@bp.app_context_processor
def inject_global_variables():
    """Injeta variáveis globais em todos os templates deste blueprint."""
    try:
        published_landing_pages = LandingPage.query.filter_by(is_published=True).order_by(LandingPage.title).all()
        site_settings = Settings.query.first()
        return dict(
            nav_landing_pages=published_landing_pages,
            site_settings=site_settings
        )
    except Exception as e:
        print(f"Erro ao injetar variáveis globais no blueprint 'main': {e}")
        return dict(nav_landing_pages=[], site_settings=None)
