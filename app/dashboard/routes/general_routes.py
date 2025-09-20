# app/dashboard/routes/general_routes.py

# --- Imports Essenciais ---
from datetime import date, timedelta
from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import func, extract, or_

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import Post, Category, LandingPage, Lead, Client, Settings, Popup
from app.forms import SettingsForm

# --- ROTAS GERAIS DO DASHBOARD ---

@bp.route('/')
@login_required
def index():
    """Página principal do dashboard com estatísticas do sistema."""
    # Stats de Conteúdo
    total_posts = Post.query.count()
    posts_publicados = Post.query.filter_by(is_published=True).count()
    total_categories = Category.query.count()
    total_landing_pages = LandingPage.query.count()

    # Stats de Leads
    total_leads = Lead.query.count()
    leads_by_status = {
        status: count for status, count in db.session.query(
            Lead.status, func.count(Lead.id)
        ).group_by(Lead.status).all()
    }

    # Stats de Clientes e Aniversários
    total_clients = Client.query.count()
    settings = Settings.query.first()
    notification_days = settings.birthday_notification_days if settings else 30
    today = date.today()
    end_date = today + timedelta(days=notification_days)
    
    today_ordinal = today.timetuple().tm_yday
    end_date_ordinal = end_date.timetuple().tm_yday
    birthday_ordinal = extract('doy', Client.child_date_of_birth)

    if today_ordinal <= end_date_ordinal:
        # Intervalo não cruza a virada do ano
        upcoming_birthdays_count = Client.query.filter(
            birthday_ordinal.between(today_ordinal, end_date_ordinal)
        ).count()
    else:
        # Intervalo cruza a virada do ano (ex: Dezembro-Janeiro)
        upcoming_birthdays_count = Client.query.filter(
            or_(birthday_ordinal >= today_ordinal, birthday_ordinal <= end_date_ordinal)
        ).count()

    # Dicionário final de estatísticas para o template
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
    return render_template('dashboard/index.html', stats=stats, title="Dashboard")

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Página para gerenciar as configurações globais do site."""
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


# --- PROCESSADOR DE CONTEXTO ---
# Esta função injeta variáveis em todos os templates renderizados pelo blueprint.

@bp.app_context_processor
def inject_global_variables():
    """Injeta variáveis globais em todos os templates do dashboard."""
    try:
        published_landing_pages = LandingPage.query.filter_by(is_published=True).order_by(LandingPage.title).all()
        site_settings = Settings.query.first()
        active_popup = Popup.query.filter_by(is_active=True).first()

        return dict(
            nav_landing_pages=published_landing_pages,
            site_settings=site_settings,
            active_popup=active_popup
        )
    except Exception as e:
        print(f"Erro ao injetar variáveis globais: {e}")
        return dict(nav_landing_pages=[], site_settings=None, active_popup=None)