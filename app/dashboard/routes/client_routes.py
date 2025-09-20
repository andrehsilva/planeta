# app/dashboard/routes/client_routes.py

# --- Imports Essenciais ---
from datetime import date, timedelta
from io import BytesIO
from urllib.parse import quote
import pandas as pd
from flask import render_template, flash, redirect, url_for, request, Response
from flask_login import login_required
from sqlalchemy import or_, extract

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import Client, Settings, ClientService
from app.forms import ClientForm, ClientServiceForm

# --- Rotas Principais de Clientes ---

@bp.route('/clients')
@login_required
def list_clients():
    """Lista todos os clientes com filtros e status de aniversário."""
    # 1. Obter os parâmetros da URL para filtros e paginação
    page = request.args.get('page', 1, type=int)
    birthday_filter = request.args.get('birthday_filter')
    search_filter = request.args.get('search', '')

    # 2. Construir a query base
    query = Client.query

    # Aplica o filtro de aniversariantes do próximo mês
    if birthday_filter == 'true':
        today = date.today()
        next_month = today.month + 1 if today.month < 12 else 1
        query = query.filter(extract('month', Client.child_date_of_birth) == next_month)

    # Aplica o filtro de busca textual
    if search_filter:
        search_term = f'%{search_filter}%'
        query = query.filter(
            or_(
                Client.child_name.ilike(search_term),
                Client.parent1_name.ilike(search_term),
                Client.parent2_name.ilike(search_term),
                Client.contact_phone.ilike(search_term),
                Client.email.ilike(search_term)
            )
        )

    # 3. Executar a query e paginar os resultados
    clients_pagination = query.order_by(Client.child_name).paginate(
        page=page, per_page=15, error_out=False
    )

    # 4. Processar status de aniversário para os clientes da página atual
    settings = Settings.query.first()
    notification_days = settings.birthday_notification_days if settings else 30
    today = date.today()
    birthday_today_ids = set()
    upcoming_birthday_ids = set()
    birthday_status_map = {}

    for client in clients_pagination.items:
        dob = client.child_date_of_birth
        birthday_this_year = date(today.year, dob.month, dob.day)

        if birthday_this_year < today:
            birthday_status_map[client.id] = "Já fez"
        elif birthday_this_year == today:
            birthday_status_map[client.id] = "Parabéns!"
            birthday_today_ids.add(client.id)
        else:
            birthday_status_map[client.id] = "Ainda não fez"
            # Verifica se o aniversário está dentro da janela de notificação
            if today < birthday_this_year <= today + timedelta(days=notification_days):
                upcoming_birthday_ids.add(client.id)

    # 5. Renderizar o template com todos os dados
    return render_template(
        'dashboard/clients.html',
        clients_pagination=clients_pagination,
        birthday_filter_active=(birthday_filter == 'true'),
        search=search_filter,
        birthday_today_ids=birthday_today_ids,
        upcoming_birthday_ids=upcoming_birthday_ids,
        birthday_status_map=birthday_status_map
    )


@bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def add_client():
    """Formulário para adicionar um novo cliente."""
    form = ClientForm()
    if form.validate_on_submit():
        new_client = Client()
        form.populate_obj(new_client) # Popula o objeto com os dados do form
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
        form.populate_obj(client)
        db.session.commit()
        flash('Dados do cliente atualizados com sucesso!', 'success')
        return redirect(url_for('dashboard.list_clients'))
    return render_template('dashboard/manage_client.html', form=form, title="Editar Cliente")

@bp.route('/clients/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    """Rota para excluir um cliente."""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('dashboard.list_clients'))

# --- Rotas de Histórico de Serviço ---

@bp.route('/clients/<int:client_id>/history', methods=['GET', 'POST'])
@login_required
def client_history(client_id):
    """Página de histórico de serviços de um cliente específico."""
    client = Client.query.get_or_404(client_id)
    form = ClientServiceForm()

    if form.validate_on_submit():
        new_service = ClientService(client_id=client.id)
        form.populate_obj(new_service)
        db.session.add(new_service)
        db.session.commit()
        flash('Novo serviço registrado com sucesso!', 'success')
        return redirect(url_for('dashboard.client_history', client_id=client.id))

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
    client_id = service.client_id
    db.session.delete(service)
    db.session.commit()
    flash('Registro de serviço excluído com sucesso!', 'success')
    return redirect(url_for('dashboard.client_history', client_id=client_id))

# --- Rotas de Ações (WhatsApp, Exportação) ---

@bp.route('/clients/<int:client_id>/send_birthday_message')
@login_required
def send_birthday_message(client_id):
    """Prepara e redireciona para o WhatsApp com a mensagem de aniversário."""
    client = Client.query.get_or_404(client_id)
    settings = Settings.query.first()
    
    if not settings or not settings.birthday_congrats_message:
        flash('Configure a mensagem de aniversário primeiro nas Configurações.', 'warning')
        return redirect(url_for('dashboard.list_clients'))

    message = settings.birthday_congrats_message
    message = message.replace('[NOME_CRIANCA]', client.child_name)
    message = message.replace('[NOME_RESPONSAVEL]', client.parent1_name)
    
    phone_number = ''.join(filter(str.isdigit, client.contact_phone))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={quote(message)}"
    
    return redirect(whatsapp_url)

@bp.route('/clients/<int:client_id>/send_whatsapp')
@login_required
def send_client_message(client_id):
    """Prepara e redireciona para o WhatsApp com a mensagem padrão para clientes."""
    client = Client.query.get_or_404(client_id)
    settings = Settings.query.first()

    if not settings or not settings.client_whatsapp_message:
        flash('Configure a mensagem de WhatsApp para clientes nas Configurações.', 'warning')
        return redirect(url_for('dashboard.list_clients'))

    message = settings.client_whatsapp_message
    message = message.replace('[NOME_CRIANCA]', client.child_name)
    message = message.replace('[NOME_RESPONSAVEL]', client.parent1_name)
    
    phone_number = ''.join(filter(str.isdigit, client.contact_phone))
    whatsapp_url = f"https://wa.me/55{phone_number}?text={quote(message)}"
    
    return redirect(whatsapp_url)

@bp.route('/clients/export')
@login_required
def export_clients():
    """Exporta todos os clientes para um arquivo Excel (.xlsx)."""
    clients = Client.query.all()
    data = [c.to_dict() for c in clients] # Supondo um método .to_dict() no modelo Client
    df = pd.DataFrame(data)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Clientes')
    writer.close() # pd.__version__ < 1.4: writer.save()
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=clientes.xlsx"}
    )