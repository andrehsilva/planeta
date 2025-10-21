# app/utils.py
import os
import secrets
from flask import current_app
from werkzeug.utils import secure_filename

def delete_file_from_uploads(filename):
    """
    Exclui um arquivo da pasta de UPLOAD_FOLDER se ele existir
    e não for o 'default.jpg'.
    """
    if not filename or filename == 'default.jpg':
        return
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # É uma boa prática logar esse erro em um sistema real
        print(f"Erro ao deletar o arquivo {filename}: {e}")

def save_picture(form_picture_data):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture_data.filename)
    picture_fn = random_hex + f_ext

    upload_folder = current_app.config['UPLOAD_FOLDER']
    picture_path = os.path.join(upload_folder, picture_fn)

    # LOG para debug
    print(f"📁 SALVANDO IMAGEM EM: {picture_path}")
    print(f"📁 UPLOAD_FOLDER configurado: {upload_folder}")
    print(f"📁 Pasta existe? {os.path.exists(upload_folder)}")
    
    os.makedirs(upload_folder, exist_ok=True)
    form_picture_data.save(picture_path)
    
    # Verifica se foi salvo
    print(f"✅ Imagem salva? {os.path.exists(picture_path)}")
    
    return picture_fn

def save_video(form_video_data):
    """
    Salva um vídeo do formulário na pasta UPLOAD_FOLDER
    e retorna o nome do arquivo.
    """
    random_hex = secrets.token_hex(8)
    video_fn = secure_filename(form_video_data.filename)
    video_name = random_hex + '_' + video_fn
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    video_path = os.path.join(upload_folder, video_name)
    
    os.makedirs(upload_folder, exist_ok=True)
    
    form_video_data.save(video_path)
    return video_name

def get_media_url(filename):
    """
    Retorna a URL correta para um arquivo de mídia baseado no ambiente
    """
    if not filename:
        return ""
    
    # Em desenvolvimento, usa o caminho static/uploads
    if current_app.config.get('DEBUG'):
        return url_for('static', filename=f'uploads/{filename}')
    # Em produção, usa o caminho /media/
    else:
        return f"/media/{filename}"