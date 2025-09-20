# app/models.py
from app.extensions import db
from datetime import date, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Tabela de associação para a relação Muitos-para-Muitos entre Post e Category
post_categories = db.Table('post_categories',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

# app/models.py

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # ✅ ALTERADO: O padrão para novos registros agora é 'colaborador'
    role = db.Column(db.String(20), nullable=False, default='colaborador')

    # ✅ NOVO CAMPO ADICIONADO
    is_approved = db.Column(db.Boolean, nullable=False, default=False, server_default='f')
    
    # Seus campos existentes
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Métodos de senha (sem alterações)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    # ✅ NOVA PROPRIEDADE ADICIONADA
    # Facilita a verificação se o usuário é admin
    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(100), nullable=True, default='default.jpg') # Armazena o nome do arquivo da imagem
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='posts')

    video_filename = db.Column(db.String(100), nullable=True)
    
    # Relação com Vídeos da Galeria (Um-para-Muitos)
    gallery_videos = db.relationship('Video', backref='post', lazy=True, cascade="all, delete-orphan")
    
    # Relação com Categorias (Muitos-para-Muitos)
    categories = db.relationship('Category', secondary=post_categories, lazy='subquery',
        backref=db.backref('posts', lazy=True))
        
    # Relação com a Galeria de Imagens (Um-para-Muitos)
    gallery_images = db.relationship('Image', backref='post', lazy=True, cascade="all, delete-orphan")

    # --- CAMPOS DE SEO ---
    meta_description = db.Column(db.String(160))
    is_published = db.Column(db.Boolean, default=False)
    
    # --- NOVOS CAMPOS ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.title}>'

# --- NOVO MODEL: CATEGORY ---
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

    # --- NOVOS CAMPOS ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True) # Legenda opcional
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    # --- NOVOS CAMPOS ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Image {self.filename}>'
    



class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    child_name = db.Column(db.String(100), nullable=True)
    child_age = db.Column(db.Integer, nullable=True)
    service_of_interest = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Novo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lead {self.parent_name}>'
    


class LandingPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, comment="Título interno da página para organização.")
    slug = db.Column(db.String(120), unique=True, nullable=False, comment="A URL final da página (ex: /lp/nome-da-campanha).")
    is_published = db.Column(db.Boolean, default=False, index=True)

    # --- Seção Principal (Hero) ---
    hero_title = db.Column(db.String(200))
    hero_subtitle = db.Column(db.Text)
    hero_image = db.Column(db.String(100), nullable=True)
    hero_cta_text = db.Column(db.String(50), comment="Texto do botão, ex: 'Saiba Mais'")
    hero_cta_link = db.Column(db.String(255), comment="Link de destino do botão")

    # --- Seção de Conteúdo ---
    content_title = db.Column(db.String(200))
    content_body = db.Column(db.Text) # Pode ser usado com um editor de texto rico
    content_image = db.Column(db.String(100), nullable=True) # <-- ADICIONE ESTA LINHA


    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LandingPage {self.title}>'
    


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Dados da Criança
    child_name = db.Column(db.String(150), nullable=False)
    child_date_of_birth = db.Column(db.Date, nullable=False)

    # Dados dos Responsáveis
    parent1_name = db.Column(db.String(150), nullable=False)
    parent1_phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True, index=True)
    parent2_name = db.Column(db.String(150), nullable=True) # Opcional
    parent2_phone = db.Column(db.String(20), nullable=True) # Opcional

    # Endereço
    address_street = db.Column(db.String(200), nullable=True)
    address_number = db.Column(db.String(20), nullable=True)
    address_neighborhood = db.Column(db.String(100), nullable=True)
    address_city = db.Column(db.String(100), nullable=True)
    address_cep = db.Column(db.String(10), nullable=True)
    
    # Telefone de Contato Principal
    contact_phone = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com os serviços do cliente
    services = db.relationship('ClientService', backref='client', lazy=True, cascade="all, delete-orphan")

    # Propriedade para calcular a idade dinamicamente
    @property
    def age(self):
        if not self.child_date_of_birth:
            return None
        today = date.today()
        # Calcula a idade
        age = today.year - self.child_date_of_birth.year - ((today.month, today.day) < (self.child_date_of_birth.month, self.child_date_of_birth.day))
        return age
    
    def __repr__(self):
        return f'<Client {self.child_name}>'



class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # ✅ CAMPOS ADICIONADOS PARA SEO
    business_name = db.Column(db.String(100), default="Planeta Imaginário")
    site_description = db.Column(db.Text, default="Espaço de recreação infantil e festas de aniversário temáticas no Shopping.")
   
    
    # Mensagens WhatsApp
    lead_whatsapp_message = db.Column(db.Text, default="Olá [NOME_LEAD], recebemos seu contato e em breve retornaremos!")
    client_whatsapp_message = db.Column(db.Text, default="Olá [NOME_RESPONSAVEL], tudo bem? Somos da Planeta Imaginário.")
    birthday_congrats_message = db.Column(db.Text, default="Olá [NOME_RESPONSAVEL]! Passando para desejar um feliz aniversário para o(a) [NOME_CRIANCA]! 🎉🎈")

    # Regras de Aniversário
    birthday_notification_days = db.Column(db.Integer, default=30, comment="Número de dias de antecedência para destacar aniversariantes.")

    # --- ✅ NOVOS CAMPOS PARA O RODAPÉ ---
    footer_address = db.Column(db.Text, default="Jundiaí Shopping - Piso G3, Loja S113\nJundiaí, SP")
    footer_phone = db.Column(db.String(50), default="(11) 95080-3725")
    footer_email = db.Column(db.String(120), default="contato@planetaimaginario.com")
    footer_instagram_link = db.Column(db.String(255), default="#")
    footer_facebook_link = db.Column(db.String(255), default="#")
    footer_whatsapp_link = db.Column(db.String(255), default="#")
    footer_copyright_text = db.Column(db.String(200), default="© Planeta Imaginário. Todos os direitos reservados.")

    def __repr__(self):
        return f'<Settings {self.id}>'
    


# ✅ Adicione esta nova classe inteira no final do arquivo
class ClientService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(150), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    observation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Chave estrangeira para linkar com o cliente
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    def __repr__(self):
        return f'<ClientService {self.service_name} for client {self.client_id}>'
    


# app/models.py

class HomePageContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # ✅ NOVO CAMPO PARA ARMAZENAR A ORDEM
    section_order = db.Column(
        db.Text,
        nullable=False,
        default='hero,services,values,structure,videos,blog,cta,location',
        server_default='hero,services,values,structure,videos,blog,cta,location'
    )
    
    # --- Seção Hero ---
    show_hero_section = db.Column(db.Boolean, default=True)
    hero_background_color_from = db.Column(db.String(20), default='#4f46e5')
    hero_background_color_to = db.Column(db.String(20), default='#f97316')
    hero_badge_text = db.Column(db.String(200))
    hero_title = db.Column(db.String(200))
    hero_subtitle = db.Column(db.Text)
    hero_whatsapp_button_text = db.Column(db.String(100))
    hero_whatsapp_button_link = db.Column(db.String(255))
    hero_highlight_text = db.Column(db.String(200))

    # --- Seção "O que oferecemos" ---
    show_services_section = db.Column(db.Boolean, default=True)
    services_section_tagline = db.Column(db.String(100))
    services_section_title = db.Column(db.String(200))
    services_section_subtitle = db.Column(db.Text)
    services_card1_icon = db.Column(db.String(10))
    services_card1_title = db.Column(db.String(100))
    services_card1_text = db.Column(db.Text)
    services_card1_item1 = db.Column(db.String(100))
    services_card1_item2 = db.Column(db.String(100))
    services_card1_item3 = db.Column(db.String(100))
    services_card1_cta_text = db.Column(db.String(50))
    services_card1_cta_link = db.Column(db.String(255))
    services_card2_icon = db.Column(db.String(10))
    services_card2_title = db.Column(db.String(100))
    services_card2_text = db.Column(db.Text)
    services_card2_item1 = db.Column(db.String(100))
    services_card2_item2 = db.Column(db.String(100))
    services_card2_item3 = db.Column(db.String(100))
    services_card2_cta_text = db.Column(db.String(50))
    services_card2_cta_link = db.Column(db.String(255))
    services_card3_icon = db.Column(db.String(10))
    services_card3_title = db.Column(db.String(100))
    services_card3_text = db.Column(db.Text)
    services_card3_item1 = db.Column(db.String(100))
    services_card3_item2 = db.Column(db.String(100))
    services_card3_item3 = db.Column(db.String(100))
    services_card3_cta_text = db.Column(db.String(50))
    services_card3_cta_link = db.Column(db.String(255))

    # --- Seção "Por que nos escolher" ---
    show_values_section = db.Column(db.Boolean, default=True)
    values_section_tagline = db.Column(db.String(100))
    values_section_title = db.Column(db.String(200))
    values_section_subtitle = db.Column(db.Text)
    values_card1_icon = db.Column(db.String(10))
    values_card1_title = db.Column(db.String(100))
    values_card1_text = db.Column(db.Text)
    values_card2_icon = db.Column(db.String(10))
    values_card2_title = db.Column(db.String(100))
    values_card2_text = db.Column(db.Text)
    values_card3_icon = db.Column(db.String(10))
    values_card3_title = db.Column(db.String(100))
    values_card3_text = db.Column(db.Text)

    # --- Seção "Infraestrutura" ---
    show_structure_section = db.Column(db.Boolean, default=True)
    structure_section_tagline = db.Column(db.String(100))
    structure_section_title = db.Column(db.String(200))
    structure_section_subtitle = db.Column(db.Text)
    structure_feature1_title = db.Column(db.String(100))
    structure_feature1_text = db.Column(db.Text)
    structure_feature2_title = db.Column(db.String(100))
    structure_feature2_text = db.Column(db.Text)
    structure_images = db.relationship('StructureImage', backref='homepage', lazy=True, cascade="all, delete-orphan")
    structure_videos = db.relationship('StructureVideo', backref='homepage', lazy=True, cascade="all, delete-orphan")

    # --- Seção "Diário de bordo" (Blog) ---
    show_blog_section = db.Column(db.Boolean, default=True)
    blog_section_tagline = db.Column(db.String(100))
    blog_section_title = db.Column(db.String(200))
    blog_section_subtitle = db.Column(db.Text)
    blog_cta_text = db.Column(db.String(100))
    
    # --- Seção CTA Final ---
    show_cta_section = db.Column(db.Boolean, default=True)
    cta_title = db.Column(db.String(200))
    cta_subtitle = db.Column(db.Text)
    cta_whatsapp_button_text = db.Column(db.String(100))
    cta_form_button_text = db.Column(db.String(100))
    
    # --- Seção "Localização" ---
    show_location_section = db.Column(db.Boolean, default=True)
    location_section_tagline = db.Column(db.String(100))
    location_section_title = db.Column(db.String(200))
    location_section_subtitle = db.Column(db.Text)
    location_card_title = db.Column(db.String(100))
    location_address_title = db.Column(db.String(50))
    location_address_text = db.Column(db.Text)
    location_phone_title = db.Column(db.String(50))
    location_phone_text = db.Column(db.String(50))
    location_hours_title = db.Column(db.String(50))
    location_hours_text = db.Column(db.Text)
    location_gmaps_button_text = db.Column(db.String(50))
    location_gmaps_link = db.Column(db.String(255))
    location_image_alt = db.Column(db.String(200))

    # --- Seção "Nossos Vídeos" (NOVA SEÇÃO) ---
    show_videos_section = db.Column(db.Boolean, default=True)
    videos_section_title = db.Column(db.String(200))
    videos_section_video1 = db.Column(db.String(100), nullable=True)
    videos_section_video2 = db.Column(db.String(100), nullable=True)
    videos_section_video3 = db.Column(db.String(100), nullable=True)

class StructureImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(100), nullable=False) # Ex: 'Campo de Futebol'
    homepage_content_id = db.Column(db.Integer, db.ForeignKey('home_page_content.id'), nullable=False)


class StructureVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(100), nullable=False)
    homepage_content_id = db.Column(db.Integer, db.ForeignKey('home_page_content.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StructureVideo {self.filename}>'

# app/models.py

# ... (outros modelos) ...

# app/models.py

class Popup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, comment="Título interno para identificação no dashboard.")
    image_filename = db.Column(db.String(100), nullable=False, comment="Nome do arquivo da imagem.")
    target_url = db.Column(db.String(255), nullable=False, comment="Link de destino ao clicar na imagem.")
    is_active = db.Column(db.Boolean, default=False, index=True, comment="Só pode haver um popup ativo por vez.")
    
    # ✅ NOVO CAMPO ADICIONADO AQUI
    display_mode = db.Column(
        db.String(50), 
        nullable=False, 
        default='show_once', 
        comment="Modo de exibição: 'show_once' (mostrar uma vez) ou 'always_show' (mostrar sempre)."
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Popup {self.title}>'
    

# Novo modelo para vídeos da galeria de posts
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

