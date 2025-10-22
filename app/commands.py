# commands.py
import click
from flask.cli import with_appcontext
from sqlalchemy import text  # Importe 'text' para executar SQL puro
from app.extensions import db
from app.models import User, HomePageContent
import os
from .extensions import db

@click.command(name='create_admin')
@with_appcontext
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin(username, email, password):
    """
    Cria um novo usuário administrador.
    Exemplo: flask create_admin nome_admin admin@email.com senha_segura
    """
    if User.query.filter_by(username=username).first():
        click.echo(f"Erro: Usuário '{username}' já existe.")
        return
    if User.query.filter_by(email=email).first():
        click.echo(f"Erro: Email '{email}' já está em uso.")
        return

    admin_user = User(username=username, email=email, role='admin')
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    click.echo(f"Administrador '{username}' criado com sucesso!")


# ✅ NOVO COMANDO ADICIONADO AQUI
@click.command(name='db-reset-history')
@with_appcontext
def db_reset_history():
    """Apaga a tabela alembic_version para resetar o histórico de migrações."""
    try:
        db.session.execute(text('DROP TABLE IF EXISTS alembic_version;'))
        db.session.commit()
        click.echo("Histórico de migração (tabela alembic_version) removido com sucesso.")
        click.echo("Agora você pode rodar 'flask db upgrade' para criar o banco do zero.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Erro ao remover o histórico de migração: {e}")

# ✅ ADICIONE ESTE NOVO COMANDO
@click.command(name='db-drop-all')
@with_appcontext
def db_drop_all():
    """Apaga todas as tabelas do banco de dados."""
    if click.confirm('Tem certeza que quer apagar TODAS as tabelas do banco de dados? Seus dados serão perdidos.'):
        db.drop_all()
        click.echo("Todas as tabelas foram apagadas com sucesso.")


# ✅ ADICIONE ESTE NOVO COMANDO
@click.command(name='seed-homepage')
@with_appcontext
def seed_homepage():
    """Popula a tabela home_page_content com o conteúdo inicial."""
    
    # Tenta encontrar o primeiro registro de conteúdo.
    # A rota da home já deve ter criado um, então ele deve existir.
    content = HomePageContent.query.get(1)

    if not content:
        click.echo("Erro: Nenhum conteúdo da homepage encontrado para atualizar. Acesse a página inicial primeiro para criar o registro.")
        return

    # Atualizando todos os campos com os valores fornecidos
    content.hero_title='Diversão além da imaginação'
    content.hero_subtitle='Festas de aniversário temáticas e passaportes de diversão em um universo onde a imaginação não tem limites.'
    content.cta_title='Pronto para embarcar nessa aventura?'
    content.cta_subtitle='Entre em contato e vamos criar juntos momentos inesquecíveis para sua criança!'
    content.hero_badge_text='Planeta Imaginário - Jundiaí Shopping - Piso G3, Loja S113'
    content.hero_whatsapp_button_text='Fale conosco'
    content.hero_whatsapp_button_link='https://wa.me/5511950803725'
    content.hero_highlight_text='Espaço seguro e monitorado por profissionais especializados'
    content.services_section_tagline='O que oferecemos'
    content.services_section_title='Experiências inesquecíveis'
    content.services_section_subtitle='Criamos momentos mágicos que ficarão para sempre na memória das crianças e das famílias'
    content.services_card1_icon='🎂'
    content.services_card1_title='Festas de aniversário'
    content.services_card1_text='Celebre de forma única e personalizada com nossas festas temáticas que transformam sonhos em realidade.'
    content.services_card1_item1='Temas exclusivos e personalizados'
    content.services_card1_item2='Decoração temática completa'
    content.services_card1_item3='Recreação especializada'
    content.services_card1_cta_text='Solicitar orçamento'
    content.services_card1_cta_link='https://'
    content.services_card2_icon='🪪'
    content.services_card2_title='Passaporte de diversão'
    content.services_card2_text='Deixe as crianças se divertirem em um ambiente seguro enquanto você aproveita o shopping com tranquilidade.'
    content.services_card2_item1='Monitoramento por câmeras'
    content.services_card2_item2='Equipe especializada em recreação'
    content.services_card2_item3='Ambiente lúdico e seguro'
    content.services_card2_cta_text='Saiba mais'
    content.services_card2_cta_link='https://'
    content.services_card3_icon='⏰'
    content.services_card3_title='Tempo livre'
    content.services_card3_text='Momentos de lazer garantidos para as crianças aproveitarem nosso espaço mágico de forma segura e divertida, com opção a partir de 30 minutos.'
    content.services_card3_item1='Diversão monitorada por profissionais especializados'
    content.services_card3_item2='Atividades lúdicas em um ambiente seguro'
    content.services_card3_item3='Tranquilidade para os pais aproveitarem o shopping'
    content.services_card3_cta_text='Saiba mais'
    content.services_card3_cta_link='https://'
    content.values_section_tagline='Por que nos escolher'
    content.values_section_title='Missão, visão e valores'
    content.values_section_subtitle='Nosso compromisso é criar experiências que vão além da diversão'
    content.values_card1_icon='✨'
    content.values_card1_title='Missão'
    content.values_card1_text='Proporcionar experiências lúdicas e educativas que estimulem a criatividade e o desenvolvimento infantil em um ambiente seguro e mágico.'
    content.values_card2_icon='🌠'
    content.values_card2_title='Visão'
    content.values_card2_text='Ser referência em entretenimento infantil, onde cada visita se transforma em uma aventura inesquecível no universo da imaginação.'
    content.values_card3_icon='💖'
    content.values_card3_title='Valores'
    content.values_card3_text='Segurança, criatividade, inclusão e respeito pela individualidade de cada criança, criando memórias felizes para toda a família.'
    content.structure_section_tagline='Infraestrutura'
    content.structure_section_title='Um universo de possibilidades'
    content.structure_section_subtitle='Nossas instalações foram cuidadosamente projetadas para oferecer diversão, segurança e conforto em cada detalhe.'
    content.structure_feature1_title='Ambientes'
    content.structure_feature1_text='⏺ Campo de futebol\n⏺ Área de games\n⏺ Brinquedoteca\n⏺ Espaço maquiagem\n⏺ e muito mais!'
    content.structure_feature2_title='Benefícios'
    content.structure_feature2_text='Ambiente Seguro: Monitoramento 360° e equipe treinada para garantir a segurança das crianças.\nEspaço Higienizado: Limpeza constante e protocolos rigorosos de higiene em todas as áreas.\nAcessibilidade: Espaço adaptado para garantir que todas as crianças possam brincar com conforto.'
    content.blog_section_tagline='Nosso diário'
    content.blog_section_title='Diário de bordo'
    content.blog_section_subtitle='As últimas aventuras e novidades do nosso Planeta'
    content.blog_cta_text='Ver todas as aventuras'
    content.cta_whatsapp_button_text='Falar no WhatsApp'
    content.cta_form_button_text='Preencher formulário'
    content.location_section_tagline='Onde estamos'
    content.location_section_title='Venha nos visitar!'
    content.location_section_subtitle='Estamos localizados no Jundiaí Shopping, um ponto de fácil acesso no coração da cidade.'
    content.location_card_title='Informações de contato'
    content.location_address_title='📍 Endereço'
    content.location_address_text='Jundiaí Shopping - Piso G3, Loja S113<br>Av. 9 de Julho, 3333 - Jundiaí/SP'
    content.location_phone_title='📱 Telefone/WhatsApp'
    content.location_phone_text='(11) 95080-3725'
    content.location_hours_title='⏰ Funcionamento'
    content.location_hours_text='Seg a Sáb: 10h às 22h<br>Dom e Feriados: 12h às 20h'
    content.location_gmaps_button_text='Ver no Google Maps'
    content.location_gmaps_link='https://www.google.com/maps/search/?api=1&query=Planeta+Imaginario+Jundiai+Shopping'
    content.location_image_alt='Mapa da localização do Planeta Imaginário no Jundiaí Shopping'
    content.show_hero_section=True
    content.hero_background_color_from='#5448E2'
    content.hero_background_color_to='#1F2937'
    content.show_services_section=True
    content.show_values_section=True
    content.show_structure_section=True
    content.show_blog_section=True
    content.show_cta_section=True
    content.show_location_section=True

    db.session.commit()
    click.echo("Conteúdo da Homepage populado com sucesso!")

# ✅ ATUALIZE A FUNÇÃO DE REGISTRO
def register_commands(app):
    """Registra os comandos CLI com a aplicação Flask."""
    app.cli.add_command(create_admin)
    app.cli.add_command(db_reset_history)
    app.cli.add_command(db_drop_all) # Adiciona o novo comando de drop
    app.cli.add_command(seed_homepage) # Adiciona o novo comando

    @app.cli.command('fix-media-permissions')
    @with_appcontext
    def fix_media_permissions():
        """Corrige permissões da pasta media e arquivos"""
        import stat
        from flask import current_app
        
        media_path = current_app.config['UPLOAD_FOLDER']
        
        if os.path.exists(media_path):
            # Corrige permissões da pasta
            os.chmod(media_path, 0o755)
            click.echo(f"✅ Permissões da pasta corrigidas: {media_path}")
            
            # Corrige permissões dos arquivos
            for filename in os.listdir(media_path):
                filepath = os.path.join(media_path, filename)
                if os.path.isfile(filepath):
                    os.chmod(filepath, 0o644)
                    click.echo(f"✅ Permissões do arquivo corrigidas: {filename}")
            
            click.echo("🎉 Todas as permissões foram corrigidas!")
        else:
            click.echo(f"❌ Pasta não encontrada: {media_path}")

    @app.cli.command('check-config')
    @with_appcontext
    def check_config():
        """Verifica a configuração atual do UPLOAD_FOLDER"""
        from flask import current_app

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        debug_mode = current_app.config.get('DEBUG')
        env = os.environ.get('FLASK_ENV', 'default')

        click.echo(f"🔧 Configuração Atual:")
        click.echo(f"   FLASK_ENV: {env}")
        click.echo(f"   DEBUG: {debug_mode}")
        click.echo(f"   UPLOAD_FOLDER: {upload_folder}")
        click.echo(f"   Pasta existe: {os.path.exists(upload_folder) if upload_folder else 'N/A'}")

        # Verifica onde está salvando
        test_path = os.path.join(upload_folder, 'test.txt') if upload_folder else ''
        click.echo(f"   Pasta gravável: {os.access(upload_folder, os.W_OK) if upload_folder and os.path.exists(upload_folder) else 'N/A'}")


    @app.cli.command('migrate-to-media')
    @with_appcontext
    def migrate_to_media():
        """Migra arquivos de static/uploads para /app/media"""
        import shutil
        from flask import current_app

        source_dir = '/app/app/static/uploads'  # Caminho atual
        target_dir = current_app.config['UPLOAD_FOLDER']  # Caminho configurado

        click.echo(f"🔄 Migrando de: {source_dir}")
        click.echo(f"            para: {target_dir}")

        if os.path.exists(source_dir):
            # Cria pasta destino se não existir
            os.makedirs(target_dir, exist_ok=True)

            # Copia arquivos
            files_copied = 0
            for filename in os.listdir(source_dir):
                source_path = os.path.join(source_dir, filename)
                target_path = os.path.join(target_dir, filename)

                if os.path.isfile(source_path):
                    shutil.copy2(source_path, target_path)
                    files_copied += 1
                    click.echo(f"✅ Copiado: {filename}")

            click.echo(f"🎉 Migração concluída! {files_copied} arquivos movidos.")

            # Verifica se os arquivos estão acessíveis
            if os.path.exists(target_dir):
                media_files = len([f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))])
                click.echo(f"📁 Agora temos {media_files} arquivos em {target_dir}")
        else:
            click.echo("❌ Pasta source não encontrada.")

    @app.cli.command('clean-orphaned-files')
    @with_appcontext
    def clean_orphaned_files():
        """Remove arquivos orphaned da pasta static/uploads"""
        source_dir = '/app/app/static/uploads'
        
        if os.path.exists(source_dir):
            files = os.listdir(source_dir)
            if files:
                click.echo(f"🗑️  Encontrados {len(files)} arquivos em {source_dir}")
                if click.confirm('Deseja remover estes arquivos?'):
                    for filename in files:
                        filepath = os.path.join(source_dir, filename)
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                            click.echo(f"❌ Removido: {filename}")
                    click.echo("✅ Limpeza concluída!")
            else:
                click.echo("✅ Pasta static/uploads já está vazia")
        else:
            click.echo("❌ Pasta static/uploads não existe")
