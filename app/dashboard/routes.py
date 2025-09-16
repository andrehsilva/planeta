import os
import secrets
from flask import render_template, flash, redirect, url_for, abort, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from slugify import slugify
from werkzeug.datastructures import FileStorage


from sqlalchemy import func, extract, or_

from urllib.parse import quote

import pandas as pd
from flask import Response
from io import BytesIO

from app.dashboard import bp
from app.extensions import db
from app.models import Post, Category, User, Image, LandingPage, Lead, Client, Settings, ClientService, HomePageContent, StructureImage , Popup
from app.forms import CategoryForm, PostForm, LeadForm, LandingPageForm, ClientForm, ImportForm, SettingsForm, ClientServiceForm,  HomePageContentForm, PopupForm, AdminResetPasswordForm, ChangePasswordForm

from datetime import date, timedelta

from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403) # Erro de "Proibido"
        return f(*args, **kwargs)
    return decorated_function



@bp.route('/users')
@login_required
@admin_required
def list_users():
    """Lista todos os usuários para o admin."""
    users = User.query.order_by(User.username).all()
    return render_template('dashboard/users.html', users=users, title="Gerenciar Usuários")

@bp.route('/users/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Aprova um usuário pendente."""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'O usuário {user.username} foi aprovado com sucesso!', 'success')
    return redirect(url_for('dashboard.list_users'))

@bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Alterna o papel de um usuário entre admin e colaborador."""
    user = User.query.get_or_404(user_id)
    # Impede que o admin remova o próprio status de admin
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
    """Admin redefine a senha de um usuário."""
    user = User.query.get_or_404(user_id)
    form = AdminResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(f'A senha de {user.username} foi redefinida com sucesso.', 'success')
        return redirect(url_for('dashboard.list_users'))
    return render_template('dashboard/reset_password.html', form=form, title=f"Redefinir Senha de {user.username}", user=user)

# --- ROTA PARA O PRÓPRIO USUÁRIO MUDAR A SENHA ---

@bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Página para o usuário logado mudar sua própria senha."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Sua senha atual está incorreta.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('dashboard/change_password.html', form=form, title="Alterar Minha Senha")


@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Deleta um usuário."""
    user = User.query.get_or_404(user_id)

    # CRÍTICO: Impede que um administrador delete a própria conta
    if user.id == current_user.id:
        flash('Você не pode excluir sua própria conta de administrador.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário "{user.username}" foi excluído com sucesso.', 'success')
    return redirect(url_for('dashboard.list_users'))



# --- ROTA DE CONFIGURAÇÕES ---
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Como só teremos uma linha de configuração, pegamos a primeira ou criamos uma.
    settings_obj = Settings.query.first()
    if not settings_obj:
        settings_obj = Settings()
        db.session.add(settings_obj)
        db.session.commit()

    form = SettingsForm(obj=settings_obj)
    if form.validate_on_submit():
        form.populate_obj(settings_obj)
        db.session.commit()
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('dashboard.settings'))

    return render_template('dashboard/settings.html', form=form, title="Configurações")


# --- FUNÇÃO AUXILIAR PARA SALVAR IMAGENS ---
def save_picture(form_picture_data):
    """Gera um nome de arquivo seguro e único e salva a imagem."""
    random_hex = secrets.token_hex(8)
    picture_fn = secure_filename(form_picture_data.filename)
    picture_name = random_hex + '_' + picture_fn
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_name)
    
    form_picture_data.save(picture_path)
    return picture_name

# --- ROTAS PRINCIPAIS DO DASHBOARD ---





@bp.route('/')
@login_required
def index():
    """Página principal do dashboard, agora com estatísticas completas."""
    # --- Stats de Conteúdo e Landing Pages (Mantido) ---
    total_posts = Post.query.count()
    posts_publicados = Post.query.filter_by(is_published=True).count()
    total_categories = Category.query.count()
    total_landing_pages = LandingPage.query.count()

    # --- Stats de Leads (Mantido) ---
    total_leads = Lead.query.count()
    lead_status_counts = db.session.query(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status).all()
    leads_by_status = {status: count for status, count in lead_status_counts}

    # --- ✅ Stats de Clientes e Aniversários (CORRIGIDO) ---
    total_clients = Client.query.count()
    
    # Busca a configuração de dias de antecedência para o aviso
    settings = Settings.query.first()
    notification_days = settings.birthday_notification_days if settings else 30
    
    # Calcula a data final para a contagem de aniversariantes
    today = date.today()
    end_date = today + timedelta(days=notification_days)
    
    # --- LÓGICA DE ANIVERSÁRIO PORTÁTIL USANDO EXTRACT ---
    # Converte as datas para um formato numérico "dia do ano" (1-366)
    # Isso resolve o problema de virada de ano de forma simples e eficiente.
    today_ordinal = today.timetuple().tm_yday
    end_date_ordinal = end_date.timetuple().tm_yday

    # Extrai o dia do ano da data de nascimento diretamente no banco de dados
    birthday_ordinal = extract('doy', Client.child_date_of_birth)

    if today_ordinal <= end_date_ordinal:
        # Caso normal: o intervalo não cruza o fim do ano (ex: 15/Maio - 15/Junho)
        upcoming_birthdays_count = Client.query.filter(
            birthday_ordinal.between(today_ordinal, end_date_ordinal)
        ).count()
    else:
        # Caso complexo: o intervalo cruza a virada do ano (ex: 15/Dez - 15/Jan)
        # Conta aniversários do dia de hoje até o fim do ano (>=) OU do começo do ano até a data final (<=)
        upcoming_birthdays_count = Client.query.filter(
            or_(
                birthday_ordinal >= today_ordinal,
                birthday_ordinal <= end_date_ordinal
            )
        ).count()

    # --- Dicionário final de estatísticas ---
    stats = {
        'total_posts': total_posts,
        'posts_publicados': posts_publicados,
        'posts_rascunho': total_posts - posts_publicados,
        'total_categories': total_categories,
        'total_landing_pages': total_landing_pages,
        'total_leads': total_leads,
        'leads_by_status': leads_by_status,
        'total_clients': total_clients,
        'upcoming_birthdays': upcoming_birthdays_count
    }
    return render_template('dashboard/index.html', stats=stats)
# --- ROTAS DE GERENCIAMENTO DE POSTS ---

@bp.route('/posts')
@login_required
def list_posts():
    """Página para listar e gerenciar todas as postagens com filtros."""
    page = request.args.get('page', 1, type=int)
    
    # --- LÓGICA DE FILTRO ---
    query = Post.query
    
    # Filtro por categoria
    category_filter = request.args.get('category', type=int)
    if category_filter:
        query = query.join(Post.categories).filter(Category.id == category_filter)
        
    # Filtro por status
    status_filter = request.args.get('status', type=str)
    if status_filter == 'published':
        query = query.filter(Post.is_published == True)
    elif status_filter == 'draft':
        query = query.filter(Post.is_published == False)
    
    # Buscamos todas as categorias para popular o dropdown do filtro
    all_categories = Category.query.order_by(Category.name).all()

    posts_pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Passamos os filtros ativos para o template para manter o estado do formulário
    active_filters = {
        'category': category_filter,
        'status': status_filter
    }
    
    return render_template('dashboard/posts.html', 
                           posts_pagination=posts_pagination,
                           all_categories=all_categories,
                           filters=active_filters)


@bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def add_post():
    """Formulário para adicionar uma nova postagem."""
    form = PostForm()
    if form.validate_on_submit():
        cover_image_filename = 'default.jpg'
        if isinstance(form.cover_image.data, FileStorage):
            cover_image_filename = save_picture(form.cover_image.data)

        new_post = Post(
            title=form.title.data,
            slug=slugify(form.title.data),
            content=form.content.data,
            author=current_user,
            categories=form.categories.data,
            meta_description=form.meta_description.data,
            is_published=form.is_published.data,
            cover_image=cover_image_filename
        )
        db.session.add(new_post)
        
        if form.gallery_images.data:
            for image_file in form.gallery_images.data:
                if isinstance(image_file, FileStorage):
                    gallery_image_filename = save_picture(image_file)
                    new_image = Image(filename=gallery_image_filename, post=new_post)
                    db.session.add(new_image)

        db.session.commit()
        flash('Postagem criada com sucesso!', 'success')
        # Redireciona para a nova lista de posts
        return redirect(url_for('dashboard.list_posts'))
    return render_template('dashboard/manage_post.html', form=form, title='Nova Postagem')

@bp.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Formulário para editar uma postagem existente."""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        if isinstance(form.cover_image.data, FileStorage):
            post.cover_image = save_picture(form.cover_image.data)

        post.title = form.title.data
        post.slug = slugify(form.title.data)
        post.content = form.content.data
        post.categories = form.categories.data
        post.meta_description = form.meta_description.data
        post.is_published = form.is_published.data
        
        if form.gallery_images.data:
            for image_file in form.gallery_images.data:
                if isinstance(image_file, FileStorage):
                    gallery_image_filename = save_picture(image_file)
                    new_image = Image(filename=gallery_image_filename, post=post)
                    db.session.add(new_image)

        db.session.commit()
        flash('Postagem atualizada com sucesso!', 'success')
        # Redireciona para a nova lista de posts
        return redirect(url_for('dashboard.list_posts'))
    return render_template('dashboard/manage_post.html', form=form, title='Editar Postagem', post=post)

@bp.route('/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Rota para excluir uma postagem."""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Postagem excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_posts'))


# --- ROTAS DE GERENCIAMENTO DE CATEGORIAS ---

@bp.route('/categories')
@login_required
def list_categories():
    """Lista todas as categorias com paginação e filtro de busca."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '') # Pega o termo de busca
    
    query = Category.query
    if search:
        # Filtra por nome, ignorando maiúsculas/minúsculas
        query = query.filter(Category.name.ilike(f'%{search}%'))

    categories_pagination = query.order_by(Category.name).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('dashboard/categories.html', 
                           categories_pagination=categories_pagination,
                           search=search)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
def add_category():
    """Formulário para adicionar uma nova categoria."""
    form = CategoryForm()
    if form.validate_on_submit():
        new_category = Category(
            name=form.name.data,
            slug=slugify(form.name.data)
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_categories'))
    return render_template('dashboard/manage_category.html', form=form, title='Nova Categoria')

@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Formulário para editar uma categoria existente."""
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
    """Rota para excluir uma categoria."""
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_categories'))


# --- ROTAS DE GERENCIAMENTO DE IMAGENS ---

@bp.route('/images/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Rota para excluir uma imagem da galeria."""
    image = Image.query.get_or_404(image_id)
    post_id = image.post.id

    try:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        flash(f'Erro ao deletar o arquivo de imagem: {e}', 'danger')

    db.session.delete(image)
    db.session.commit()
    flash('Imagem da galeria foi excluída.', 'success')
    return redirect(url_for('dashboard.edit_post', post_id=post_id))




# --- ROTAS DE GERENCIAMENTO DE LANDING PAGES ---

@bp.route('/landingpages')
@login_required
def list_landing_pages():
    """Lista todas as Landing Pages criadas."""
    page = request.args.get('page', 1, type=int)
    landing_pages_pagination = LandingPage.query.order_by(LandingPage.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('dashboard/list_landing_pages.html',
                           landing_pages_pagination=landing_pages_pagination)


@bp.route('/landingpages/new', methods=['GET', 'POST'])
@login_required
def add_landing_page():
    """Formulário para criar uma nova Landing Page."""
    form = LandingPageForm()
    if form.validate_on_submit():
        new_lp = LandingPage(
            title=form.title.data,
            slug=slugify(form.title.data) # Gera slug a partir do título
        )

        # Preenche os dados do formulário no modelo
        for field in form:
            if hasattr(new_lp, field.name):
                setattr(new_lp, field.name, field.data)

        if isinstance(form.hero_image.data, FileStorage):
            hero_image_filename = save_picture(form.hero_image.data)
            new_lp.hero_image = hero_image_filename

        if isinstance(form.content_image.data, FileStorage):
        
            content_image_filename = save_picture(form.content_image.data)
            new_lp.content_image = content_image_filename


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
        lp.title = form.title.data
        lp.slug = slugify(form.title.data) # Atualiza o slug se o título mudar

        for field in form:
            if hasattr(lp, field.name):
                 # Não sobrescreva o campo da imagem se nenhum novo arquivo for enviado
                if field.type != 'FileField':
                    setattr(lp, field.name, field.data)

        if isinstance(form.content_image.data, FileStorage):
            lp.content_image = save_picture(form.content_image.data)
            
        if isinstance(form.hero_image.data, FileStorage):
            lp.hero_image = save_picture(form.hero_image.data)

        db.session.commit()
        flash('Landing Page atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard.list_landing_pages'))
    return render_template('dashboard/manage_landing_page.html', form=form, title='Editar Landing Page', landing_page=lp)


@bp.route('/landingpages/delete/<int:lp_id>', methods=['POST'])
@login_required
def delete_landing_page(lp_id):
    """Rota para excluir uma Landing Page."""
    lp = LandingPage.query.get_or_404(lp_id)
    # Aqui você pode querer adicionar lógica para remover imagens associadas do servidor
    db.session.delete(lp)
    db.session.commit()
    flash('Landing Page excluída com sucesso!', 'success')
    return redirect(url_for('dashboard.list_landing_pages'))


# --- ROTA PARA O DASHBOARD DE LEADS ---
# app/dashboard/routes.py

# ... outros imports ...
from sqlalchemy import or_ # 👈 Adicione este import no topo do arquivo

# ... (outras rotas) ...


# --- ROTA PARA O DASHBOARD DE LEADS (ATUALIZADA) ---
@bp.route('/leads')
@login_required
def leads():
    """
    Exibe uma lista paginada e filtrável de todos os leads capturados.
    """
    page = request.args.get('page', 1, type=int)
    
    # --- ✅ Novos filtros ---
    status_filter = request.args.get('status', '', type=str)
    search_filter = request.args.get('search', '', type=str)

    # Inicia a query base
    query = Lead.query

    # --- ✅ Lógica de filtro atualizada ---
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if search_filter:
        search_term = f'%{search_filter}%'
        # Procura no nome do responsável OU no nome da criança (se existir)
        query = query.filter(
            or_(
                Lead.parent_name.ilike(search_term),
                Lead.child_name.ilike(search_term)
            )
        )
    
    # Ordena e pagina os resultados
    leads_pagination = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # Lista de status para popular o dropdown do filtro
    all_statuses = ['Novo', 'Contactado', 'Não Atendeu', 'Reagendar', 'Descartado']
    
    # Armazena os filtros aplicados para preencher o formulário
    filters = {
        'status': status_filter,
        'search': search_filter
    }

    return render_template(
        'dashboard/leads.html', 
        leads_pagination=leads_pagination,
        all_statuses=all_statuses, # ✅ Envia a lista de status
        filters=filters,
        title="Dashboard de Leads"
    )



@bp.route('/leads/<int:lead_id>/update_status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """
    Recebe um POST para atualizar o status de um lead específico.
    """
    lead = Lead.query.get_or_404(lead_id)
    new_status = request.form.get('status')

    # Lista de status válidos para segurança
    valid_statuses = ['Novo', 'Contactado', 'Não Atendeu', 'Reagendar', 'Descartado']
    
    if new_status and new_status in valid_statuses:
        lead.status = new_status
        db.session.commit()
        flash(f'Status do lead "{lead.parent_name}" atualizado para "{new_status}".', 'success')
    else:
        flash('Status inválido selecionado.', 'danger')
        
    return redirect(url_for('dashboard.leads'))




###Clients
# app/dashboard/routes.py

@bp.route('/clients')
@login_required
def list_clients():
    """Lista todos os clientes com filtros e status de aniversário (versão final)."""
    # 1. Obter os parâmetros da URL
    page = request.args.get('page', 1, type=int)
    birthday_filter = request.args.get('birthday_filter')
    search_filter = request.args.get('search', '')

    # 2. Construir a query base com os filtros
    query = Client.query

    if birthday_filter == 'true':
        today = date.today()
        next_month = today.month + 1 if today.month < 12 else 1
        query = query.filter(extract('month', Client.child_date_of_birth) == next_month)

    if search_filter:
        search_term = f'%{search_filter}%'
        query = query.filter(
            or_(
                Client.child_name.ilike(search_term),
                Client.parent1_name.ilike(search_term),
                Client.parent2_name.ilike(search_term),
                Client.contact_phone.ilike(search_term),
                Client.parent1_phone.ilike(search_term),
                Client.parent2_phone.ilike(search_term),
                Client.email.ilike(search_term)
            )
        )

    # 3. Executar a query e paginar os resultados
    clients_pagination = query.order_by(Client.child_name).paginate(
        page=page, per_page=15, error_out=False
    )

    # 4. Processar os aniversariantes e status do ano
    settings = Settings.query.first()
    notification_days = settings.birthday_notification_days if settings else 30
    today = date.today()

    birthday_today_ids = set()
    upcoming_birthday_ids = set()
    birthday_status_map = {} # ✅ Dicionário para guardar o status do aniversário no ano

    for client in clients_pagination.items:
        dob = client.child_date_of_birth
        
        # Define a data do aniversário deste ano para comparação
        birthday_this_year = date(today.year, dob.month, dob.day)

        # ✅ Lógica CORRIGIDA E UNIFICADA
        if birthday_this_year < today:
            birthday_status_map[client.id] = "Já fez"
        elif birthday_this_year == today:
            birthday_status_map[client.id] = "Parabéns!"  # Define o status para o badge
            birthday_today_ids.add(client.id)             # E TAMBÉM adiciona ao set para o destaque da linha
        else:
            birthday_status_map[client.id] = "Ainda não fez"
            for i in range(1, notification_days + 1):
                check_date = today + timedelta(days=i)
                if dob.month == check_date.month and dob.day == check_date.day:
                    upcoming_birthday_ids.add(client.id)
                    break

    # 5. Renderizar o template com todos os dados
    return render_template(
        'dashboard/clients.html',
        clients_pagination=clients_pagination,
        birthday_filter_active=(birthday_filter == 'true'),
        search=search_filter,
        birthday_today_ids=birthday_today_ids,
        upcoming_birthday_ids=upcoming_birthday_ids,
        birthday_status_map=birthday_status_map # ✅ Envia o novo dicionário para o template
    )


@bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def add_client():
    """Formulário para adicionar um novo cliente."""
    form = ClientForm()
    if form.validate_on_submit():
        new_client = Client(
            child_name=form.child_name.data,
            child_date_of_birth=form.child_date_of_birth.data,
            parent1_name=form.parent1_name.data,
            parent1_phone=form.parent1_phone.data,
            email=form.email.data,
            parent2_name=form.parent2_name.data,
            parent2_phone=form.parent2_phone.data,
            contact_phone=form.contact_phone.data,
            address_street=form.address_street.data,
            address_number=form.address_number.data,
            address_neighborhood=form.address_neighborhood.data,
            address_city=form.address_city.data,
            address_cep=form.address_cep.data
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard.list_clients'))
    return render_template('dashboard/manage_client.html', form=form, title="Novo Cliente")

@bp.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    """Formulário para editar um cliente existente."""
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        # Preenche os dados do formulário no objeto client
        form.populate_obj(client)
        db.session.commit()
        flash('Dados do cliente atualizados com sucesso!', 'success')
        return redirect(url_for('dashboard.list_clients'))
    return render_template('dashboard/manage_client.html', form=form, title="Editar Cliente")



@bp.route('/clients/<int:client_id>/send_birthday_message')
@login_required
def send_birthday_message(client_id):
    client = Client.query.get_or_404(client_id)
    settings = Settings.query.first()
    
    if not settings:
        flash('Configure a mensagem de aniversário primeiro.', 'warning')
        return redirect(url_for('dashboard.list_clients'))

    # Substitui os placeholders
    message = settings.birthday_congrats_message
    message = message.replace('[NOME_CRIANCA]', client.child_name)
    message = message.replace('[NOME_RESPONSAVEL]', client.parent1_name)
    
    # Codifica a mensagem para a URL
    encoded_message = quote(message)
    
    phone_number = ''.join(filter(str.isdigit, client.contact_phone))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={encoded_message}"
    
    flash(f'Preparando mensagem de parabéns para {client.child_name}.', 'info')
    return redirect(whatsapp_url)



@bp.route('/clients/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    """Rota para excluir um cliente."""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('dashboard.list_clients'))



# importação e exportação

@bp.route('/clients/export')
@login_required
def export_clients():
    """Exporta todos os clientes para um arquivo Excel."""
    clients = Client.query.all()

    # Converte os dados para um formato que o pandas pode ler (lista de dicionários)
    data = [
        {
            'Nome Criança': c.child_name, 'Data de Nascimento': c.child_date_of_birth,
            'Nome Responsável 1': c.parent1_name, 'Telefone Resp. 1': c.parent1_phone,
            'Email': c.email, 
            'Nome Responsável 2': c.parent2_name, 'Telefone Resp. 2': c.parent2_phone,
            'Telefone Principal': c.contact_phone,
            'Rua': c.address_street, 'Número': c.address_number, 'Bairro': c.address_neighborhood,
            'Cidade': c.address_city, 'CEP': c.address_cep
        } for c in clients
    ]

    df = pd.DataFrame(data)

    # Cria um buffer de memória para salvar o arquivo Excel
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Clientes')
    writer.close()
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=clientes.xlsx"}
    )



@bp.route('/leads/<int:lead_id>/send_whatsapp')
@login_required
def send_lead_message(lead_id):
    """Prepara e redireciona para o WhatsApp com a mensagem de lead."""
    lead = Lead.query.get_or_404(lead_id)
    settings = Settings.query.first()

    if not settings or not settings.lead_whatsapp_message:
        flash('Configure a mensagem de WhatsApp para leads primeiro nas Configurações.', 'warning')
        return redirect(url_for('dashboard.leads'))

    # Substitui os placeholders
    message = settings.lead_whatsapp_message.replace('[NOME_LEAD]', lead.parent_name)
    
    # Codifica a mensagem para a URL
    encoded_message = quote(message)
    
    phone_number = ''.join(filter(str.isdigit, lead.whatsapp))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={encoded_message}"
    
    return redirect(whatsapp_url)


@bp.route('/clients/<int:client_id>/send_whatsapp')
@login_required
def send_client_message(client_id):
    """Prepara e redireciona para o WhatsApp com a mensagem de cliente."""
    client = Client.query.get_or_404(client_id)
    settings = Settings.query.first()

    if not settings or not settings.client_whatsapp_message:
        flash('Configure a mensagem de WhatsApp para clientes primeiro nas Configurações.', 'warning')
        return redirect(url_for('dashboard.list_clients'))

    # Substitui os placeholders
    message = settings.client_whatsapp_message
    message = message.replace('[NOME_CRIANCA]', client.child_name)
    message = message.replace('[NOME_RESPONSAVEL]', client.parent1_name)
    
    # Codifica a mensagem para a URL
    encoded_message = quote(message)
    
    phone_number = ''.join(filter(str.isdigit, client.contact_phone))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={encoded_message}"
    
    return redirect(whatsapp_url)



@bp.route('/clients/<int:client_id>/history', methods=['GET', 'POST'])
@login_required
def client_history(client_id):
    """Página de histórico de um cliente específico."""
    client = Client.query.get_or_404(client_id)
    form = ClientServiceForm()

    if form.validate_on_submit():
        new_service = ClientService(
            service_name=form.service_name.data,
            service_date=form.service_date.data,
            observation=form.observation.data,
            client_id=client.id
        )
        db.session.add(new_service)
        db.session.commit()
        flash('Novo serviço registrado com sucesso!', 'success')
        return redirect(url_for('dashboard.client_history', client_id=client.id))

    # Query para pegar os serviços em ordem decrescente de data
    services = ClientService.query.filter_by(client_id=client.id).order_by(ClientService.service_date.desc()).all()
    
    return render_template('dashboard/client_history.html', 
                           title=f"Histórico de {client.child_name}", 
                           client=client, 
                           form=form,
                           services=services)


@bp.route('/clients/history/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    """Edita um registro de serviço existente."""
    service = ClientService.query.get_or_404(service_id)
    form = ClientServiceForm(obj=service)
    
    if form.validate_on_submit():
        form.populate_obj(service)
        db.session.commit()
        flash('Registro de serviço atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard.client_history', client_id=service.client_id))
        
    return render_template('dashboard/manage_service.html',
                           title="Editar Registro de Serviço",
                           form=form)


@bp.route('/clients/history/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    """Exclui um registro de serviço."""
    service = ClientService.query.get_or_404(service_id)
    client_id = service.client_id # Guarda o ID do cliente antes de deletar
    db.session.delete(service)
    db.session.commit()
    flash('Registro de serviço excluído com sucesso!', 'success')
    return redirect(url_for('dashboard.client_history', client_id=client_id))





@bp.route('/homepage', methods=['GET', 'POST'])
@login_required
def edit_homepage():
    content = HomePageContent.query.first()
    if not content:
        # Se for a primeira vez, cria o objeto de conteúdo com valores padrão do modelo
        content = HomePageContent()
        db.session.add(content)
        db.session.commit()

    form = HomePageContentForm(obj=content)

    if form.validate_on_submit():
        # O populate_obj preenche todos os campos de texto do modelo com os dados do formulário
        form.populate_obj(content)
        
        # --- ✅ 1. SALVAR A NOVA ORDEM ---
        # Pega a nova ordem do campo escondido que criamos no template
        new_order = request.form.get('section_order')
        if new_order:
            content.section_order = new_order
        
        # Processa as novas imagens da galeria (se houver alguma)
        if form.gallery_images.data:
            for image_file in form.gallery_images.data:
                if isinstance(image_file, FileStorage) and image_file.filename != '':
                    filename = save_picture(image_file)
                    # A legenda será o nome do arquivo por padrão
                    caption = os.path.splitext(image_file.filename)[0].replace('_', ' ').title()
                    new_img = StructureImage(filename=filename, caption=caption, homepage_content_id=content.id)
                    db.session.add(new_img)

        db.session.commit()
        flash('Conteúdo e ordem da página inicial atualizados com sucesso!', 'success')
        return redirect(url_for('dashboard.edit_homepage'))
    
    # --- ✅ 2. ENVIAR A ORDEM ATUAL PARA O TEMPLATE ---
    # Lê a ordem do banco, transforma em uma lista e envia para o manage_homepage.html
    ordered_sections_admin = content.section_order.split(',')
    
    return render_template(
        'dashboard/manage_homepage.html',
        form=form,
        title="Editar Página Inicial",
        content=content,
        ordered_sections_admin=ordered_sections_admin # Passa a lista ordenada para o template
    )

@bp.route('/homepage/image/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_structure_image(image_id):
    """Exclui uma imagem da galeria da homepage."""
    image = StructureImage.query.get_or_404(image_id)
    
    # Lógica para deletar o arquivo físico do servidor
    try:
        image_path = os.path.join(current_app.root_path, 'static', 'uploads', image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        flash(f'Erro ao deletar o arquivo de imagem: {e}', 'danger')

    db.session.delete(image)
    db.session.commit()
    flash('Imagem da galeria foi excluída.', 'success')
    return redirect(url_for('dashboard.edit_homepage'))




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

        # Salva a imagem
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

        # Se uma nova imagem foi enviada, salva e atualiza o nome do arquivo
        if form.image.data:
            # (Opcional: deletar a imagem antiga do servidor)
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
    """Deleta um popup."""
    popup = Popup.query.get_or_404(popup_id)
    # (Opcional: deletar o arquivo de imagem do servidor)
    db.session.delete(popup)
    db.session.commit()
    flash('Popup deletado com sucesso!', 'success')
    return redirect(url_for('dashboard.list_popups'))


# app/main/routes.py


@bp.app_context_processor
def inject_global_variables():
    """Injeta variáveis globais em todos os templates."""
    try:
        published_landing_pages = LandingPage.query.filter_by(is_published=True).order_by(LandingPage.title).all()
        site_settings = Settings.query.first()
        # ✅ BUSCA O POPUP ATIVO
        active_popup = Popup.query.filter_by(is_active=True).first()

        return dict(
            nav_landing_pages=published_landing_pages,
            site_settings=site_settings,
            active_popup=active_popup  # ✅ INJETA O POPUP
        )
    except Exception as e:
        print(f"Erro ao injetar variáveis globais: {e}")
        return dict(nav_landing_pages=[], site_settings=None, active_popup=None)