# app/dashboard/routes/post_routes.py

# --- Imports Essenciais ---
import os
import secrets
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from slugify import slugify

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import Post, Category, Image, Video
from app.forms import PostForm, CategoryForm

# --- Funções Auxiliares (Helpers) ---
# NOTA: Para uma organização mais avançada no futuro, estas funções poderiam
# viver em um único arquivo de 'helpers' para evitar duplicação.
# Por enquanto, mantê-las aqui torna cada módulo de rotas autossuficiente.

def _delete_file(filename):
    """Deleta um arquivo da pasta de uploads, ignorando o 'default.jpg'."""
    if not filename or filename == 'default.jpg':
        return
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Erro ao deletar o arquivo {filename}: {e}")

def save_picture(form_picture_data):
    """Gera um nome de arquivo seguro e único e salva a imagem."""
    random_hex = secrets.token_hex(8)
    picture_fn = secure_filename(form_picture_data.filename)
    picture_name = random_hex + '_' + picture_fn
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_name)
    form_picture_data.save(picture_path)
    return picture_name

def save_video(form_video_data):
    """Gera um nome de arquivo seguro e único e salva o vídeo."""
    random_hex = secrets.token_hex(8)
    video_fn = secure_filename(form_video_data.filename)
    video_name = random_hex + '_' + video_fn
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video_name)
    form_video_data.save(video_path)
    return video_name

# --- ROTAS DE GERENCIAMENTO DE POSTS ---

@bp.route('/posts')
@login_required
def list_posts():
    """Lista todas as postagens com filtros por categoria e status."""
    page = request.args.get('page', 1, type=int)
    query = Post.query
    
    category_filter = request.args.get('category', type=int)
    if category_filter:
        query = query.join(Post.categories).filter(Category.id == category_filter)
        
    status_filter = request.args.get('status')
    if status_filter == 'published':
        query = query.filter(Post.is_published == True)
    elif status_filter == 'draft':
        query = query.filter(Post.is_published == False)
    
    posts_pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    all_categories = Category.query.order_by(Category.name).all()
    active_filters = {'category': category_filter, 'status': status_filter}
    
    return render_template('dashboard/posts.html', 
                           posts_pagination=posts_pagination,
                           all_categories=all_categories,
                           filters=active_filters)

@bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def add_post():
    """Formulário para criar uma nova postagem."""
    form = PostForm()
    if form.validate_on_submit():
        cover_image_filename = 'default.jpg'
        if isinstance(form.cover_image.data, FileStorage):
            cover_image_filename = save_picture(form.cover_image.data)

        video_filename = None
        if isinstance(form.main_video.data, FileStorage):
            video_filename = save_video(form.main_video.data)

        new_post = Post(
            title=form.title.data,
            slug=slugify(form.title.data),
            content=form.content.data,
            author=current_user,
            categories=form.categories.data,
            meta_description=form.meta_description.data,
            is_published=form.is_published.data,
            cover_image=cover_image_filename,
            video_filename=video_filename
        )
        db.session.add(new_post)
        
        # Adiciona imagens da galeria
        for image_file in form.gallery_images.data:
            if isinstance(image_file, FileStorage):
                new_image = Image(filename=save_picture(image_file), post=new_post)
                db.session.add(new_image)
        
        # Adiciona vídeos da galeria
        for video_file in form.gallery_videos.data:
            if isinstance(video_file, FileStorage):
                new_video = Video(filename=save_video(video_file), post=new_post)
                db.session.add(new_video)

        db.session.commit()
        flash('Postagem criada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_posts'))
        
    return render_template('dashboard/manage_post.html', form=form, title='Nova Postagem')

@bp.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Formulário para editar uma postagem existente."""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        # Lógica de atualização/remoção da imagem de capa
        if isinstance(form.cover_image.data, FileStorage):
            _delete_file(post.cover_image)
            post.cover_image = save_picture(form.cover_image.data)
        elif form.remove_cover_image.data:
            _delete_file(post.cover_image)
            post.cover_image = 'default.jpg'

        # Lógica de atualização/remoção do vídeo principal
        if isinstance(form.main_video.data, FileStorage):
            _delete_file(post.video_filename)
            post.video_filename = save_video(form.main_video.data)
        elif form.remove_main_video.data:
            _delete_file(post.video_filename)
            post.video_filename = None
        
        # Atualiza os campos de texto e relacionamentos
        post.title = form.title.data
        post.slug = slugify(form.title.data)
        post.content = form.content.data
        post.categories = form.categories.data
        post.meta_description = form.meta_description.data
        post.is_published = form.is_published.data
        
        # Adiciona novas imagens/vídeos à galeria (não remove os existentes)
        for image_file in form.gallery_images.data:
            if isinstance(image_file, FileStorage):
                db.session.add(Image(filename=save_picture(image_file), post=post))
        
        for video_file in form.gallery_videos.data:
            if isinstance(video_file, FileStorage):
                db.session.add(Video(filename=save_video(video_file), post=post))

        db.session.commit()
        flash('Postagem atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_posts'))
        
    return render_template('dashboard/manage_post.html', form=form, title='Editar Postagem', post=post)

@bp.route('/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Exclui uma postagem e todos os seus arquivos de mídia associados."""
    post = Post.query.get_or_404(post_id)
    
    # Deleta arquivos de mídia antes de deletar o post
    _delete_file(post.cover_image)
    _delete_file(post.video_filename)
    for image in post.gallery_images: _delete_file(image.filename)
    for video in post.gallery_videos: _delete_file(video.filename)

    db.session.delete(post)
    db.session.commit()
    flash('Postagem excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_posts'))

# --- ROTAS DE GERENCIAMENTO DE MÍDIA DE POSTS ---

@bp.route('/images/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Exclui uma imagem específica da galeria de um post."""
    image = Image.query.get_or_404(image_id)
    post_id = image.post.id
    _delete_file(image.filename)
    db.session.delete(image)
    db.session.commit()
    flash('Imagem da galeria foi excluída.', 'success')
    return redirect(url_for('dashboard.edit_post', post_id=post_id))

@bp.route('/videos/delete/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    """Exclui um vídeo específico da galeria de um post."""
    video = Video.query.get_or_404(video_id)
    post_id = video.post.id
    _delete_file(video.filename)
    db.session.delete(video)
    db.session.commit()
    flash('Vídeo da galeria foi excluído.', 'success')
    return redirect(url_for('dashboard.edit_post', post_id=post_id))

# --- ROTAS DE GERENCIAMENTO DE CATEGORIAS ---

@bp.route('/categories')
@login_required
def list_categories():
    """Lista todas as categorias com busca e paginação."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Category.query
    if search:
        query = query.filter(Category.name.ilike(f'%{search}%'))
    categories_pagination = query.order_by(Category.name).paginate(page=page, per_page=10, error_out=False)
    return render_template('dashboard/categories.html', 
                           categories_pagination=categories_pagination,
                           search=search)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
def add_category():
    """Formulário para criar uma nova categoria."""
    form = CategoryForm()
    if form.validate_on_submit():
        new_category = Category(name=form.name.data, slug=slugify(form.name.data))
        db.session.add(new_category)
        db.session.commit()
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_categories'))
    return render_template('dashboard/manage_category.html', form=form, title='Nova Categoria')

@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Formulário para editar uma categoria."""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = slugify(form.name.data)
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_categories'))
    return render_template('dashboard/manage_category.html', form=form, title='Editar Categoria')

@bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Exclui uma categoria."""
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_categories'))