# app/dashboard/routes/homepage_routes.py

# --- Imports Essenciais ---
import os
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required

# --- Imports do Projeto ---
from app.dashboard import bp
from app.extensions import db
from app.models import HomePageContent, StructureImage, StructureVideo
from app.forms import (
    HeroSectionForm, ServicesSectionForm, ValuesSectionForm,
    StructureSectionForm, VideosSectionForm, BlogSectionForm,
    CtaSectionForm, LocationSectionForm, SectionOrderForm
)
# --- IMPORTAÇÃO CENTRALIZADA DAS FUNÇÕES DE UPLOAD ---
from app.utils import save_picture, save_video, delete_file_from_uploads


# --- ROTA PRINCIPAL PARA EXIBIR A PÁGINA DE GERENCIAMENTO ---

@bp.route('/homepage', methods=['GET'])
@login_required
def edit_homepage():
    """
    Exibe a página de gerenciamento da homepage, carregando todos os formulários.
    """
    content = HomePageContent.query.first_or_404()
    
    # Instancia todos os formulários com os dados atuais do banco
    forms = {
        'order': SectionOrderForm(),
        'hero': HeroSectionForm(obj=content),
        'services': ServicesSectionForm(obj=content),
        'values': ValuesSectionForm(obj=content),
        'structure': StructureSectionForm(obj=content),
        'videos': VideosSectionForm(obj=content),
        'blog': BlogSectionForm(obj=content),
        'cta': CtaSectionForm(obj=content),
        'location': LocationSectionForm(obj=content)
    }

    ordered_sections_admin = content.section_order.split(',') if content.section_order else []
    
    return render_template(
        'dashboard/manage_homepage.html',
        title="Editar Página Inicial",
        content=content,
        forms=forms,
        ordered_sections_admin=ordered_sections_admin
    )

# --- ROTAS DE 'POST' PARA SALVAR CADA SEÇÃO INDIVIDUALMENTE ---

@bp.route('/homepage/order', methods=['POST'])
@login_required
def update_homepage_order():
    """Salva a nova ordem das seções."""
    content = HomePageContent.query.first_or_404()
    new_order = request.form.get('section_order')
    if new_order:
        content.section_order = new_order
        db.session.commit()
        flash('Ordem das seções atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/hero', methods=['POST'])
@login_required
def update_hero_section():
    content = HomePageContent.query.first_or_404()
    form = HeroSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "Topo da Página" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/services', methods=['POST'])
@login_required
def update_services_section():
    content = HomePageContent.query.first_or_404()
    form = ServicesSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "O que oferecemos" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/values', methods=['POST'])
@login_required
def update_values_section():
    content = HomePageContent.query.first_or_404()
    form = ValuesSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "Por que nos escolher" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/structure', methods=['POST'])
@login_required
def update_structure_section():
    """
    Processa o formulário da seção 'Infraestrutura'.
    """
    content = HomePageContent.query.first_or_404()
    form = StructureSectionForm()

    if form.validate_on_submit():
        # Atualiza campos de texto e booleanos
        content.show_structure_section = form.show_structure_section.data
        content.structure_section_tagline = form.structure_section_tagline.data
        content.structure_section_title = form.structure_section_title.data
        content.structure_section_subtitle = form.structure_section_subtitle.data
        content.structure_feature1_title = form.structure_feature1_title.data
        content.structure_feature1_text = form.structure_feature1_text.data
        content.structure_feature2_title = form.structure_feature2_title.data
        content.structure_feature2_text = form.structure_feature2_text.data

        # Processa as novas imagens da galeria
        if form.gallery_images.data:
            for image_file in form.gallery_images.data:
                if image_file:
                    filename = save_picture(image_file)
                    caption = os.path.splitext(image_file.filename)[0].replace('_', ' ').title()
                    new_image = StructureImage(filename=filename, caption=caption, homepage_content_id=content.id)
                    db.session.add(new_image)
        
        db.session.add(content)
        db.session.commit()
        flash('Seção "Infraestrutura" atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard.edit_homepage'))
    
    else:
        # Em caso de falha na validação, recarrega a página com os erros
        flash('Erro de validação na Seção Infraestrutura. Verifique os campos.', 'danger')
        forms = {
            'order': SectionOrderForm(),
            'hero': HeroSectionForm(obj=content),
            'services': ServicesSectionForm(obj=content),
            'values': ValuesSectionForm(obj=content),
            'structure': form,  # Usa o formulário com erros
            'videos': VideosSectionForm(obj=content),
            'blog': BlogSectionForm(obj=content),
            'cta': CtaSectionForm(obj=content),
            'location': LocationSectionForm(obj=content)
        }
        ordered_sections_admin = content.section_order.split(',') if content.section_order else []
        return render_template(
            'dashboard/manage_homepage.html',
            title="Editar Página Inicial",
            content=content,
            forms=forms,
            ordered_sections_admin=ordered_sections_admin
        )

@bp.route('/homepage/videos', methods=['POST'])
@login_required
def update_videos_section():
    content = HomePageContent.query.first_or_404()
    form = VideosSectionForm()
    if form.validate_on_submit():
        content.show_videos_section = form.show_videos_section.data
        content.videos_section_title = form.videos_section_title.data
        
        # Processa os arquivos de vídeo
        for i in range(1, 4):
            video_field = getattr(form, f'videos_section_video{i}')
            remove_field = getattr(form, f'remove_videos_section_video{i}')
            content_attr = f'videos_section_video{i}'
            
            if video_field.data:
                delete_file_from_uploads(getattr(content, content_attr))
                setattr(content, content_attr, save_video(video_field.data))
            elif remove_field.data:
                delete_file_from_uploads(getattr(content, content_attr))
                setattr(content, content_attr, None)

        db.session.add(content)
        db.session.commit()
        flash('Seção "Nossos Vídeos" atualizada com sucesso!', 'success')
    else:
        flash('Erro de validação na Seção Nossos Vídeos. Verifique os campos.', 'danger')

    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/blog', methods=['POST'])
@login_required
def update_blog_section():
    content = HomePageContent.query.first_or_404()
    form = BlogSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "Blog" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/cta', methods=['POST'])
@login_required
def update_cta_section():
    content = HomePageContent.query.first_or_404()
    form = CtaSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "CTA Final" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/location', methods=['POST'])
@login_required
def update_location_section():
    content = HomePageContent.query.first_or_404()
    form = LocationSectionForm()
    if form.validate_on_submit():
        form.populate_obj(content)
        db.session.commit()
        flash('Seção "Localização" atualizada com sucesso!', 'success')
    return redirect(url_for('dashboard.edit_homepage'))


# --- ROTAS DE DELEÇÃO ---

@bp.route('/homepage/image/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_structure_image(image_id):
    image = StructureImage.query.get_or_404(image_id)
    delete_file_from_uploads(image.filename)
    db.session.delete(image)
    db.session.commit()
    flash('Imagem da galeria foi excluída.', 'success')
    return redirect(url_for('dashboard.edit_homepage'))

@bp.route('/homepage/video/delete/<int:video_id>', methods=['POST'])
@login_required
def delete_structure_video(video_id):
    video = StructureVideo.query.get_or_404(video_id)
    delete_file_from_uploads(video.filename)
    db.session.delete(video)
    db.session.commit()
    flash('Vídeo da galeria foi excluído.', 'success')
    return redirect(url_for('dashboard.edit_homepage'))
