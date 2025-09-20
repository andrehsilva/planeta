# app/dashboard/routes/leads_routes.py

# --- Imports Essenciais ---
from urllib.parse import quote
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from sqlalchemy import or_

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import Lead, Settings

# --- Rotas de Gerenciamento de Leads ---

@bp.route('/leads')
@login_required
def leads():
    """
    Exibe uma lista paginada e filtrável de todos os leads capturados.
    """
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    search_filter = request.args.get('search', '', type=str)

    query = Lead.query

    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if search_filter:
        search_term = f'%{search_filter}%'
        # Procura no nome do responsável OU no nome da criança
        query = query.filter(
            or_(
                Lead.parent_name.ilike(search_term),
                Lead.child_name.ilike(search_term)
            )
        )
    
    leads_pagination = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # Lista de status para popular o dropdown de filtro no template
    all_statuses = ['Novo', 'Contactado', 'Não Atendeu', 'Reagendar', 'Descartado']
    
    filters = {'status': status_filter, 'search': search_filter}

    return render_template(
        'dashboard/leads.html', 
        leads_pagination=leads_pagination,
        all_statuses=all_statuses,
        filters=filters,
        title="Dashboard de Leads"
    )

@bp.route('/leads/<int:lead_id>/update_status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """
    Atualiza o status de um lead específico via formulário POST.
    """
    lead = Lead.query.get_or_404(lead_id)
    new_status = request.form.get('status')
    valid_statuses = ['Novo', 'Contactado', 'Não Atendeu', 'Reagendar', 'Descartado']
    
    if new_status and new_status in valid_statuses:
        lead.status = new_status
        db.session.commit()
        flash(f'Status do lead "{lead.parent_name}" atualizado para "{new_status}".', 'success')
    else:
        flash('Status inválido selecionado.', 'danger')
        
    return redirect(url_for('dashboard.leads'))

@bp.route('/leads/<int:lead_id>/send_whatsapp')
@login_required
def send_lead_message(lead_id):
    """Prepara e redireciona para o WhatsApp com a mensagem padrão para leads."""
    lead = Lead.query.get_or_404(lead_id)
    settings = Settings.query.first()

    if not settings or not settings.lead_whatsapp_message:
        flash('Configure a mensagem de WhatsApp para leads primeiro nas Configurações.', 'warning')
        return redirect(url_for('dashboard.leads'))

    message = settings.lead_whatsapp_message.replace('[NOME_LEAD]', lead.parent_name)
    phone_number = ''.join(filter(str.isdigit, lead.whatsapp))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={quote(message)}"
    
    return redirect(whatsapp_url)