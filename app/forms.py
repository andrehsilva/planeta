# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, BooleanField, SubmitField, TextAreaField, FieldList, FormField, SelectField, HiddenField, IntegerField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, NumberRange, EqualTo
from wtforms.fields import StringField, DateField, TextAreaField, SubmitField

from app.models import Category
from wtforms import widgets
from wtforms import Form


class RegistrationForm(FlaskForm):
    """Formulário de registro para novos colaboradores."""
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirmar Senha', 
        validators=[
            DataRequired(), 
            EqualTo('password', message='As senhas devem ser iguais.')
        ]
    )
    submit = SubmitField('Registrar')

class ChangePasswordForm(FlaskForm):
    """Formulário para o usuário logado mudar sua própria senha."""
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField(
        'Confirmar Nova Senha', 
        validators=[
            DataRequired(), 
            EqualTo('new_password', message='As senhas devem ser iguais.')
        ]
    )
    submit = SubmitField('Alterar Senha')



class AdminResetPasswordForm(FlaskForm):
    """Formulário para o admin definir uma nova senha para qualquer usuário."""
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField(
        'Confirmar Nova Senha', 
        validators=[
            DataRequired(), 
            EqualTo('new_password', message='As senhas devem ser iguais.')
        ]
    )
    submit = SubmitField('Redefinir Senha')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class CategoryForm(FlaskForm):
    name = StringField('Nome da Categoria', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Salvar')

def get_categories():
    return Category.query.all()

class PostForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=5, max=150)])
    content = TextAreaField('Conteúdo', validators=[DataRequired()])
    # O campo 'categories' vai mostrar checkboxes com as categorias do banco de dados
    categories = QuerySelectMultipleField(
        'Categorias',
        query_factory=get_categories,
        get_label='name',
    )
    meta_description = TextAreaField('Descrição (SEO)', validators=[Length(max=160)])
    is_published = BooleanField('Publicado?')
    
    cover_image = FileField(
        'Imagem de Capa', 
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens são permitidas!')]
    )
    gallery_images = MultipleFileField(
        'Galeria de Imagens', 
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens são permitidas!')]
    )

    # Novo campo para vídeo principal
    main_video = FileField(
        'Vídeo Principal', 
        validators=[FileAllowed(['mp4', 'mov', 'avi', 'webm'], 'Apenas vídeos são permitidos!')]
    )
    
    # Novo campo para vídeos da galeria
    gallery_videos = MultipleFileField(
        'Vídeos da Galeria', 
        validators=[FileAllowed(['mp4', 'mov', 'avi', 'webm'], 'Apenas vídeos são permitidos!')]
    )

    # --- INÍCIO DA ALTERAÇÃO ---
    remove_cover_image = BooleanField('Remover imagem de capa atual')
    remove_main_video = BooleanField('Remover vídeo principal atual')
    # --- FIM DA ALTERAÇÃO ---

    submit = SubmitField('Salvar Postagem')



class LeadForm(FlaskForm):
    parent_name = StringField('Seu nome', validators=[DataRequired(), Length(min=2, max=100)])
    
    # ✅ Validação de E-mail Aprimorada
    email = StringField('Seu melhor e-mail', validators=[
        DataRequired(), 
        Email(message="Por favor, insira um endereço de e-mail válido.")
    ])

     # --- ✅ VALIDAÇÃO DE WHATSAPP ATUALIZADA ---
    # Aceita (XX) XXXXX-XXXX ou apenas 11 números
    whatsapp = StringField('Seu WhatsApp', validators=[
        DataRequired(), 
        Regexp(r'^(\(?\d{2}\)?[\s-]?\d{5}-?\d{4}|\d{11})$', 
               message="Formato de WhatsApp inválido.")
    ])
    
    child_name = StringField('Nome da criança', validators=[Optional(), Length(max=100)])
    
    # ✅ Validação de Idade da Criança (entre 0 e 18 anos)
    child_age = IntegerField('Idade da criança', validators=[
        Optional(), 
        NumberRange(min=0, max=18, message="Por favor, insira uma idade válida.")
    ])
    
    service_of_interest = SelectField(
        'Qual serviço você tem interesse?',
        choices=[
            ('Festa de Aniversário', 'Festa de Aniversário'),
            ('Passaporte / Hora Avulsa', 'Passaporte / Hora Avulsa'),
            ('Outro Assunto', 'Outro Assunto')
        ],
        validators=[DataRequired()]
    )
    message = TextAreaField('Sua mensagem', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enviar Mensagem')


class LandingPageForm(FlaskForm):
    title = StringField('Título da Página (para controle interno)', validators=[DataRequired(), Length(max=120)])
    is_published = BooleanField('Publicar a página?')
    
    # --- Campos da Seção Hero ---
    hero_title = StringField('Título Principal (Hero)', validators=[Optional(), Length(max=200)])
    hero_subtitle = TextAreaField('Subtítulo (Hero)', validators=[Optional()])
    hero_image = FileField('Imagem de Fundo (Hero)', validators=[FileAllowed(['jpg', 'jpeg', 'png','webp'], 'Apenas imagens são permitidas!')])
    hero_cta_text = StringField('Texto do Botão (Hero)', validators=[Optional(), Length(max=50)])
    hero_cta_link = StringField('Link do Botão (Hero)', validators=[Optional(), Length(max=255)])
    
    # --- Campos da Seção de Conteúdo ---
    content_title = StringField('Título do Conteúdo', validators=[Optional(), Length(max=200)])
    content_body = TextAreaField('Corpo do Conteúdo', validators=[Optional()])
    content_image = FileField('Imagem do Conteúdo', validators=[FileAllowed(['jpg', 'jpeg', 'png','webp'], 'Apenas imagens são permitidas!')])
    
    submit = SubmitField('Salvar Landing Page')



class ClientForm(FlaskForm):
    # Criança
    child_name = StringField('Nome da Criança', validators=[DataRequired(), Length(max=150)])
    child_date_of_birth = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])

    # Responsáveis
    parent1_name = StringField('Nome do Responsável 1', validators=[DataRequired(), Length(max=150)])
    parent1_phone = StringField('Telefone do Responsável 1', validators=[DataRequired(), Length(max=20)])
    parent2_name = StringField('Nome do Responsável 2 (Opcional)', validators=[Optional(), Length(max=150)])
    parent2_phone = StringField('Telefone do Responsável 2 (Opcional)', validators=[Optional(), Length(max=20)])

    email = StringField('Email', validators=[Optional(), Email(message="Endereço de e-mail inválido.")])
   
    # Contato Principal
    contact_phone = StringField('Telefone Principal de Contato', validators=[DataRequired(), Length(max=20)])

    # Endereço
    address_street = StringField('Rua', validators=[Optional(), Length(max=200)])
    address_number = StringField('Número', validators=[Optional(), Length(max=20)])
    address_neighborhood = StringField('Bairro', validators=[Optional(), Length(max=100)])
    address_city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    address_cep = StringField('CEP', validators=[Optional(), Length(max=10)])
    
    submit = SubmitField('Salvar Cliente')



class ImportForm(FlaskForm):
    excel_file = FileField('Arquivo Excel (.xlsx)', validators=[DataRequired(), FileAllowed(['xlsx'])])
    submit = SubmitField('Importar Clientes')


class SettingsForm(FlaskForm):
    business_name = StringField('Nome do Negócio (para SEO)')
    site_description = TextAreaField('Descrição Geral do Site (para SEO)', 
                                     description="Uma breve descrição do negócio, com até 160 caracteres.")

    lead_whatsapp_message = TextAreaField('Mensagem de WhatsApp para Leads')
    client_whatsapp_message = TextAreaField('Mensagem de WhatsApp para Clientes')
    birthday_congrats_message = TextAreaField('Mensagem de Parabéns (Aniversário)')
    birthday_notification_days = IntegerField('Avisar sobre aniversários com X dias de antecedência')
    footer_address = TextAreaField('Endereço no Rodapé')
    footer_phone = StringField('Telefone no Rodapé')
    footer_email = StringField('E-mail no Rodapé')
    footer_instagram_link = StringField('Link do Instagram')
    footer_facebook_link = StringField('Link do Facebook')
    footer_whatsapp_link = StringField('Link do WhatsApp (wa.me/...)')
    footer_copyright_text = StringField('Texto de Copyright do Rodapé')
    submit = SubmitField('Salvar Configurações')


class ClientServiceForm(FlaskForm):
    service_name = StringField('Nome do Serviço/Festa', validators=[DataRequired(message="Campo obrigatório.")])
    service_date = DateField('Data do Serviço', format='%d/%m/%Y', validators=[DataRequired(message="Campo obrigatório.")])
    observation = TextAreaField('Observações')
    submit = SubmitField('Salvar Registro')



class PopupForm(FlaskForm):
    title = StringField('Título Interno (para seu controle)', validators=[DataRequired()])
    image = FileField('Imagem do Popup', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens são permitidas!')
    ])
    target_url = StringField('Link de Destino (URL)', validators=[DataRequired()])
    
    # ✅ ESTE CAMPO ESTÁ FALTANDO NO SEU ARQUIVO
    # Adicione este campo de seleção
    display_mode = SelectField(
        'Modo de Exibição',
        choices=[
            ('show_once', 'Mostrar uma vez por sessão do navegador'),
            ('always_show', 'Mostrar em todo carregamento de página')
        ],
        validators=[DataRequired()]
    )

    is_active = BooleanField('Ativar este popup? (Isso desativará qualquer outro popup ativo)')
    submit = SubmitField('Salvar Popup')
   





# app/forms.py

# (Mantenha todos os outros imports e formulários que já existem)
# ...

# --- FORMULÁRIOS DA HOMEPAGE (REATORADOS) ---

class HeroSectionForm(FlaskForm):
    """Formulário para a seção Hero (Topo da Página)."""
    show_hero_section = BooleanField('Exibir esta seção?')
    hero_background_color_from = StringField('Cor de Início do Degradê')
    hero_background_color_to = StringField('Cor de Fim do Degradê')
    hero_badge_text = StringField('Texto do Badge de Localização')
    hero_title = StringField('Título Principal')
    hero_subtitle = TextAreaField('Subtítulo')
    hero_whatsapp_button_text = StringField('Texto do Botão WhatsApp')
    hero_whatsapp_button_link = StringField('Link do Botão WhatsApp (wa.me/...)')
    hero_highlight_text = StringField('Texto de Destaque (Espaço Seguro)')
    submit_hero = SubmitField('Salvar Seção Topo')

class ServicesSectionForm(FlaskForm):
    """Formulário para a seção "O que oferecemos"."""
    show_services_section = BooleanField('Exibir esta seção?')
    services_section_tagline = StringField('Tagline da Seção')
    services_section_title = StringField('Título da Seção')
    services_section_subtitle = TextAreaField('Subtítulo da Seção')
    # Card 1
    services_card1_icon = StringField('Ícone do Card 1 (emoji 🎂)')
    services_card1_title = StringField('Título do Card 1')
    services_card1_text = TextAreaField('Texto do Card 1')
    services_card1_item1 = StringField('Item 1 do Card 1')
    services_card1_item2 = StringField('Item 2 do Card 1')
    services_card1_item3 = StringField('Item 3 do Card 1')
    services_card1_cta_text = StringField('Texto do Link do Card 1')
    services_card1_cta_link = StringField('Link de Destino do Card 1')
    # Card 2
    services_card2_icon = StringField('Ícone do Card 2 (emoji 🪪)')
    services_card2_title = StringField('Título do Card 2')
    services_card2_text = TextAreaField('Texto do Card 2')
    services_card2_item1 = StringField('Item 1 do Card 2')
    services_card2_item2 = StringField('Item 2 do Card 2')
    services_card2_item3 = StringField('Item 3 do Card 2')
    services_card2_cta_text = StringField('Texto do Link do Card 2')
    services_card2_cta_link = StringField('Link de Destino do Card 2')
    # Card 3
    services_card3_icon = StringField('Ícone do Card 3 (emoji 🚀)')
    services_card3_title = StringField('Título do Card 3')
    services_card3_text = TextAreaField('Texto do Card 3')
    services_card3_item1 = StringField('Item 1 do Card 3')
    services_card3_item2 = StringField('Item 2 do Card 3')
    services_card3_item3 = StringField('Item 3 do Card 3')
    services_card3_cta_text = StringField('Texto do Link do Card 3')
    services_card3_cta_link = StringField('Link de Destino do Card 3')
    submit_services = SubmitField('Salvar Seção "O que oferecemos"')

class ValuesSectionForm(FlaskForm):
    """Formulário para a seção "Por que nos escolher"."""
    show_values_section = BooleanField('Exibir esta seção?')
    values_section_tagline = StringField('Tagline da Seção')
    values_section_title = StringField('Título da Seção')
    values_section_subtitle = TextAreaField('Subtítulo da Seção')
    values_card1_icon = StringField('Ícone do Card 1 (emoji ✨)')
    values_card1_title = StringField('Título do Card 1')
    values_card1_text = TextAreaField('Texto do Card 1')
    values_card2_icon = StringField('Ícone do Card 2 (emoji 🌠)')
    values_card2_title = StringField('Título do Card 2')
    values_card2_text = TextAreaField('Texto do Card 2')
    values_card3_icon = StringField('Ícone do Card 3 (emoji 💖)')
    values_card3_title = StringField('Título do Card 3')
    values_card3_text = TextAreaField('Texto do Card 3')
    submit_values = SubmitField('Salvar Seção "Por que nos escolher"')

class StructureSectionForm(FlaskForm):
    """Formulário para a seção "Infraestrutura"."""
    show_structure_section = BooleanField('Exibir esta seção?')
    structure_section_tagline = StringField('Tagline da Seção')
    structure_section_title = StringField('Título da Seção')
    structure_section_subtitle = TextAreaField('Subtítulo da Seção')
    structure_feature1_title = StringField('Destaque 1: Título')
    structure_feature1_text = TextAreaField('Destaque 1: Texto')
    structure_feature2_title = StringField('Destaque 2: Título')
    structure_feature2_text = TextAreaField('Destaque 2: Texto')
    gallery_images = MultipleFileField('Adicionar novas imagens à galeria', 
        validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens!')])
    submit_structure = SubmitField('Salvar Seção "Infraestrutura"')

class VideosSectionForm(FlaskForm):
    """Formulário para a seção "Nossos Vídeos"."""
    show_videos_section = BooleanField('Exibir esta seção?')
    videos_section_title = StringField('Título da Seção')
    videos_section_video1 = FileField('Vídeo 1', validators=[Optional(), FileAllowed(['mp4', 'mov', 'avi', 'webm'])])
    videos_section_video2 = FileField('Vídeo 2', validators=[Optional(), FileAllowed(['mp4', 'mov', 'avi', 'webm'])])
    videos_section_video3 = FileField('Vídeo 3', validators=[Optional(), FileAllowed(['mp4', 'mov', 'avi', 'webm'])])
    remove_videos_section_video1 = BooleanField('Remover Vídeo 1 atual')
    remove_videos_section_video2 = BooleanField('Remover Vídeo 2 atual')
    remove_videos_section_video3 = BooleanField('Remover Vídeo 3 atual')
    submit_videos = SubmitField('Salvar Seção "Nossos Vídeos"')

class BlogSectionForm(FlaskForm):
    """Formulário para a seção "Diário de bordo" (Blog)."""
    show_blog_section = BooleanField('Exibir esta seção?')
    blog_section_tagline = StringField('Tagline da Seção')
    blog_section_title = StringField('Título da Seção')
    blog_section_subtitle = TextAreaField('Subtítulo da Seção')
    blog_cta_text = StringField('Texto do Link "Ver todas"')
    submit_blog = SubmitField('Salvar Seção Blog')
    
class CtaSectionForm(FlaskForm):
    """Formulário para a seção "CTA Final"."""
    show_cta_section = BooleanField('Exibir esta seção?')
    cta_title = StringField('Título do CTA Final')
    cta_subtitle = TextAreaField('Subtítulo do CTA Final')
    cta_whatsapp_button_text = StringField('Texto do Botão WhatsApp')
    cta_form_button_text = StringField('Texto do Botão Formulário')
    submit_cta = SubmitField('Salvar Seção CTA')

class LocationSectionForm(FlaskForm):
    """Formulário para a seção "Localização"."""
    show_location_section = BooleanField('Exibir esta seção?')
    location_section_tagline = StringField('Tagline da Seção')
    location_section_title = StringField('Título da Seção')
    location_section_subtitle = TextAreaField('Subtítulo da Seção')
    location_card_title = StringField('Título do Card de Contato')
    location_address_title = StringField('Rótulo do Endereço')
    location_address_text = TextAreaField('Texto do Endereço')
    location_phone_title = StringField('Rótulo do Telefone')
    location_phone_text = StringField('Texto do Telefone')
    location_hours_title = StringField('Rótulo do Funcionamento')
    location_hours_text = TextAreaField('Texto do Funcionamento')
    location_gmaps_button_text = StringField('Texto do Botão Google Maps')
    location_gmaps_link = StringField('Link do Google Maps')
    location_image_alt = StringField('Texto Alternativo (alt) da Imagem do Mapa')
    submit_location = SubmitField('Salvar Seção Localização')

# Nota: O formulário de ordem das seções será um formulário HTML simples,
# não precisando de uma classe WTForms.

class SectionOrderForm(FlaskForm):
    """Formulário vazio, usado apenas para gerar o CSRF token para a reordenação."""
    pass
