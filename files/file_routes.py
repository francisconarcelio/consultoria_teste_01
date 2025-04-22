"""
Rotas para o sistema de gerenciamento de arquivos do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import uuid
import magic
import hashlib
import datetime
import mimetypes
from functools import wraps

# Importar modelos e configurações
from .file_models import Arquivo, ArquivoConteudo, ArquivoTarefa
from .file_utils import validar_arquivo, extrair_texto_arquivo, gerar_thumbnail
from .file_forms import UploadArquivoForm, PesquisaArquivoForm

# Importar extensões da aplicação
from auth import db

# Configuração do Blueprint
files_bp = Blueprint('files', __name__, template_folder='templates')

# Configurações de upload
UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

# Criar diretório de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Funções auxiliares
def allowed_file(filename):
    """
    Verifica se o arquivo possui uma extensão permitida.
    
    Args:
        filename: Nome do arquivo a ser verificado
        
    Returns:
        Boolean indicando se a extensão é permitida
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorador para verificar permissões de acesso a arquivos
def arquivo_access_required(f):
    @wraps(f)
    def decorated_function(arquivo_id, *args, **kwargs):
        arquivo = Arquivo.query.get_or_404(arquivo_id)
        
        # Verificar se o usuário tem acesso ao arquivo
        if not arquivo.publico and arquivo.usuario_id != current_user.id:
            # Verificar se o usuário pertence à mesma instituição
            if not arquivo.instituicao_id or not current_user.instituicoes:
                flash('Você não tem permissão para acessar este arquivo.', 'danger')
                return redirect(url_for('files.listar_arquivos'))
            
            # Verificar se o usuário pertence à instituição do arquivo
            user_instituicoes = [ui.instituicao_id for ui in current_user.instituicoes]
            if arquivo.instituicao_id not in user_instituicoes:
                flash('Você não tem permissão para acessar este arquivo.', 'danger')
                return redirect(url_for('files.listar_arquivos'))
        
        return f(arquivo_id, *args, **kwargs)
    return decorated_function

# Rotas
@files_bp.route('/arquivos')
@login_required
def listar_arquivos():
    """
    Lista os arquivos do usuário atual.
    """
    form = PesquisaArquivoForm()
    
    # Obter parâmetros de filtro
    tipo = request.args.get('tipo', '')
    termo = request.args.get('termo', '')
    
    # Construir query base
    query = Arquivo.query.filter(
        (Arquivo.usuario_id == current_user.id) |
        (Arquivo.publico == True)
    )
    
    # Aplicar filtros
    if tipo:
        query = query.filter(Arquivo.tipo == tipo)
    
    if termo:
        query = query.filter(
            (Arquivo.nome.ilike(f'%{termo}%')) |
            (Arquivo.conteudo_texto.ilike(f'%{termo}%'))
        )
    
    # Ordenar por data de upload (mais recentes primeiro)
    arquivos = query.order_by(Arquivo.data_upload.desc()).all()
    
    return render_template('files/listar_arquivos.html', arquivos=arquivos, form=form)

@files_bp.route('/arquivos/upload', methods=['GET', 'POST'])
@login_required
def upload_arquivo():
    """
    Página e processamento de upload de arquivos.
    """
    form = UploadArquivoForm()
    
    # Carregar instituições do usuário para o formulário
    form.instituicao_id.choices = [(0, 'Nenhuma')] + [
        (i.id, i.nome) for i in current_user.instituicoes
    ]
    
    if form.validate_on_submit():
        arquivo = form.arquivo.data
        
        if arquivo and allowed_file(arquivo.filename):
            try:
                # Gerar nome seguro e único para o arquivo
                nome_original = secure_filename(arquivo.filename)
                nome_base, extensao = os.path.splitext(nome_original)
                nome_arquivo = f"{nome_base}_{uuid.uuid4().hex}{extensao}"
                
                # Caminho completo para salvar o arquivo
                caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
                
                # Salvar arquivo temporariamente
                arquivo.save(caminho_arquivo)
                
                # Verificar tipo MIME
                mime_type = magic.Magic(mime=True).from_file(caminho_arquivo)
                
                # Validar tipo de arquivo
                if not validar_arquivo(caminho_arquivo, mime_type):
                    os.remove(caminho_arquivo)
                    flash('Tipo de arquivo não permitido.', 'danger')
                    return render_template('files/upload_arquivo.html', form=form)
                
                # Calcular hash do arquivo
                hash_arquivo = hashlib.sha256()
                with open(caminho_arquivo, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        hash_arquivo.update(byte_block)
                hash_conteudo = hash_arquivo.hexdigest()
                
                # Extrair texto do arquivo
                conteudo_texto = extrair_texto_arquivo(caminho_arquivo, mime_type)
                
                # Obter tamanho do arquivo
                tamanho_arquivo = os.path.getsize(caminho_arquivo)
                
                # Determinar tipo de arquivo para categorização
                tipo_arquivo = 'outro'
                if mime_type == 'application/pdf':
                    tipo_arquivo = 'pdf'
                elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    tipo_arquivo = 'doc'
                elif mime_type == 'text/plain':
                    tipo_arquivo = 'txt'
                
                # Criar registro de arquivo no banco de dados
                novo_arquivo = Arquivo(
                    nome=nome_original,
                    tipo=tipo_arquivo,
                    extensao=extensao[1:].lower(),
                    tamanho=tamanho_arquivo,
                    caminho=nome_arquivo,
                    hash_conteudo=hash_conteudo,
                    conteudo_texto=conteudo_texto,
                    metadados=json.dumps({
                        'mime_type': mime_type,
                        'upload_ip': request.remote_addr,
                        'user_agent': request.user_agent.string
                    }),
                    usuario_id=current_user.id,
                    instituicao_id=form.instituicao_id.data if form.instituicao_id.data != 0 else None,
                    publico=form.publico.data
                )
                
                db.session.add(novo_arquivo)
                db.session.flush()  # Para obter o ID do arquivo
                
                # Ler conteúdo do arquivo para armazenar no banco de dados
                with open(caminho_arquivo, 'rb') as f:
                    conteudo_binario = f.read()
                
                # Criar registro de conteúdo do arquivo
                arquivo_conteudo = ArquivoConteudo(
                    arquivo_id=novo_arquivo.id,
                    conteudo=conteudo_binario
                )
                
                db.session.add(arquivo_conteudo)
                db.session.commit()
                
                # Remover arquivo temporário
                os.remove(caminho_arquivo)
                
                flash('Arquivo enviado com sucesso!', 'success')
                return redirect(url_for('files.listar_arquivos'))
                
            except Exception as e:
                db.session.rollback()
                # Remover arquivo temporário em caso de erro
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
                
                flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        else:
            flash('Tipo de arquivo não permitido. Apenas PDF, DOC, DOCX e TXT são aceitos.', 'danger')
    
    return render_template('files/upload_arquivo.html', form=form)

@files_bp.route('/arquivos/<int:arquivo_id>')
@login_required
@arquivo_access_required
def visualizar_arquivo(arquivo_id):
    """
    Visualiza detalhes de um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    return render_template('files/visualizar_arquivo.html', arquivo=arquivo)

@files_bp.route('/arquivos/<int:arquivo_id>/download')
@login_required
@arquivo_access_required
def download_arquivo(arquivo_id):
    """
    Faz o download de um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    arquivo_conteudo = ArquivoConteudo.query.filter_by(arquivo_id=arquivo.id).first()
    
    if not arquivo_conteudo:
        flash('Conteúdo do arquivo não encontrado.', 'danger')
        return redirect(url_for('files.listar_arquivos'))
    
    # Criar arquivo temporário para download
    temp_path = os.path.join(UPLOAD_FOLDER, arquivo.caminho)
    with open(temp_path, 'wb') as f:
        f.write(arquivo_conteudo.conteudo)
    
    # Determinar tipo MIME
    mime_type = mimetypes.guess_type(arquivo.nome)[0] or 'application/octet-stream'
    
    # Enviar arquivo
    return send_file(
        temp_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=arquivo.nome
    )

@files_bp.route('/arquivos/<int:arquivo_id>/excluir', methods=['POST'])
@login_required
def excluir_arquivo(arquivo_id):
    """
    Exclui um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    # Verificar se o usuário é o proprietário do arquivo
    if arquivo.usuario_id != current_user.id:
        flash('Você não tem permissão para excluir este arquivo.', 'danger')
        return redirect(url_for('files.listar_arquivos'))
    
    try:
        # Excluir arquivo do banco de dados
        # A exclusão em cascata cuidará do conteúdo do arquivo
        db.session.delete(arquivo)
        db.session.commit()
        
        flash('Arquivo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir arquivo: {str(e)}', 'danger')
    
    return redirect(url_for('files.listar_arquivos'))

@files_bp.route('/arquivos/<int:arquivo_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_arquivo(arquivo_id):
    """
    Edita informações de um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    # Verificar se o usuário é o proprietário do arquivo
    if arquivo.usuario_id != current_user.id:
        flash('Você não tem permissão para editar este arquivo.', 'danger')
        return redirect(url_for('files.listar_arquivos'))
    
    form = UploadArquivoForm(obj=arquivo)
    
    # Carregar instituições do usuário para o formulário
    form.instituicao_id.choices = [(0, 'Nenhuma')] + [
        (i.id, i.nome) for i in current_user.instituicoes
    ]
    
    # Remover campo de arquivo, pois não será alterado
    delattr(form, 'arquivo')
    
    if form.validate_on_submit():
        try:
            # Atualizar informações do arquivo
            arquivo.instituicao_id = form.instituicao_id.data if form.instituicao_id.data != 0 else None
            arquivo.publico = form.publico.data
            
            db.session.commit()
            
            flash('Informações do arquivo atualizadas com sucesso!', 'success')
            return redirect(url_for('files.visualizar_arquivo', arquivo_id=arquivo.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar informações do arquivo: {str(e)}', 'danger')
    
    return render_template('files/editar_arquivo.html', form=form, arquivo=arquivo)

@files_bp.route('/arquivos/pesquisar', methods=['GET', 'POST'])
@login_required
def pesquisar_arquivos():
    """
    Pesquisa arquivos por termo e tipo.
    """
    form = PesquisaArquivoForm()
    
    if form.validate_on_submit():
        return redirect(url_for('files.listar_arquivos', tipo=form.tipo.data, termo=form.termo.data))
    
    return redirect(url_for('files.listar_arquivos'))

# Rotas da API
@files_bp.route('/api/arquivos', methods=['GET'])
@login_required
def api_listar_arquivos():
    """
    API para listar arquivos do usuário.
    """
    # Obter parâmetros de filtro
    tipo = request.args.get('tipo', '')
    termo = request.args.get('termo', '')
    
    # Construir query base
    query = Arquivo.query.filter(
        (Arquivo.usuario_id == current_user.id) |
        (Arquivo.publico == True)
    )
    
    # Aplicar filtros
    if tipo:
        query = query.filter(Arquivo.tipo == tipo)
    
    if termo:
        query = query.filter(
            (Arquivo.nome.ilike(f'%{termo}%')) |
            (Arquivo.conteudo_texto.ilike(f'%{termo}%'))
        )
    
    # Ordenar por data de upload (mais recentes primeiro)
    arquivos = query.order_by(Arquivo.data_upload.desc()).all()
    
    # Formatar resposta
    resultado = []
    for arquivo in arquivos:
        resultado.append({
            'id': arquivo.id,
            'nome': arquivo.nome,
            'tipo': arquivo.tipo,
            'extensao': arquivo.extensao,
            'tamanho': arquivo.tamanho,
            'usuario_id': arquivo.usuario_id,
            'instituicao_id': arquivo.instituicao_id,
            'publico': arquivo.publico,
            'data_upload': arquivo.data_upload.isoformat(),
            'data_atualizacao': arquivo.data_atualizacao.isoformat()
        })
    
    return jsonify(resultado)

@files_bp.route('/api/arquivos/<int:arquivo_id>', methods=['GET'])
@login_required
def api_obter_arquivo(arquivo_id):
    """
    API para obter informações de um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    # Verificar se o usuário tem acesso ao arquivo
    if not arquivo.publico and arquivo.usuario_id != current_user.id:
        # Verificar se o usuário pertence à mesma instituição
        if not arquivo.instituicao_id or not current_user.instituicoes:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se o usuário pertence à instituição do arquivo
        user_instituicoes = [ui.instituicao_id for ui in current_user.instituicoes]
        if arquivo.instituicao_id not in user_instituicoes:
            return jsonify({'error': 'Acesso negado'}), 403
    
    # Formatar resposta
    resultado = {
        'id': arquivo.id,
        'nome': arquivo.nome,
        'tipo': arquivo.tipo,
        'extensao': arquivo.extensao,
        'tamanho': arquivo.tamanho,
        'usuario_id': arquivo.usuario_id,
        'instituicao_id': arquivo.instituicao_id,
        'publico': arquivo.publico,
        'data_upload': arquivo.data_upload.isoformat(),
        'data_atualizacao': arquivo.data_atualizacao.isoformat(),
        'conteudo_texto': arquivo.conteudo_texto
    }
    
    return jsonify(resultado)

@files_bp.route('/api/arquivos', methods=['POST'])
@login_required
def api_upload_arquivo():
    """
    API para upload de arquivos.
    """
    if 'arquivo' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    arquivo = request.files['arquivo']
    
    if arquivo.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if not allowed_file(arquivo.filename):
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
    
    try:
        # Gerar nome seguro e único para o arquivo
        nome_original = secure_filename(arquivo.filename)
        nome_base, extensao = os.path.splitext(nome_original)
        nome_arquivo = f"{nome_base}_{uuid.uuid4().hex}{extensao}"
        
        # Caminho completo para salvar o arquivo
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # Salvar arquivo temporariamente
        arquivo.save(caminho_arquivo)
        
        # Verificar tipo MIME
        mime_type = magic.Magic(mime=True).from_file(caminho_arquivo)
        
        # Validar tipo de arquivo
        if not validar_arquivo(caminho_arquivo, mime_type):
            os.remove(caminho_arquivo)
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
        
        # Calcular hash do arquivo
        hash_arquivo = hashlib.sha256()
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                hash_arquivo.update(byte_block)
        hash_conteudo = hash_arquivo.hexdigest()
        
        # Extrair texto do arquivo
        conteudo_texto = extrair_texto_arquivo(caminho_arquivo, mime_type)
        
        # Obter tamanho do arquivo
        tamanho_arquivo = os.path.getsize(caminho_arquivo)
        
        # Determinar tipo de arquivo para categorização
        tipo_arquivo = 'outro'
        if mime_type == 'application/pdf':
            tipo_arquivo = 'pdf'
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            tipo_arquivo = 'doc'
        elif mime_type == 'text/plain':
            tipo_arquivo = 'txt'
        
        # Obter parâmetros adicionais
        instituicao_id = request.form.get('instituicao_id', None)
        publico = request.form.get('publico', 'false').lower() == 'true'
        
        # Criar registro de arquivo no banco de dados
        novo_arquivo = Arquivo(
            nome=nome_original,
            tipo=tipo_arquivo,
            extensao=extensao[1:].lower(),
            tamanho=tamanho_arquivo,
            caminho=nome_arquivo,
            hash_conteudo=hash_conteudo,
            conteudo_texto=conteudo_texto,
            metadados=json.dumps({
                'mime_type': mime_type,
                'upload_ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }),
            usuario_id=current_user.id,
            instituicao_id=instituicao_id,
            publico=publico
        )
        
        db.session.add(novo_arquivo)
        db.session.flush()  # Para obter o ID do arquivo
        
        # Ler conteúdo do arquivo para armazenar no banco de dados
        with open(caminho_arquivo, 'rb') as f:
            conteudo_binario = f.read()
        
        # Criar registro de conteúdo do arquivo
        arquivo_conteudo = ArquivoConteudo(
            arquivo_id=novo_arquivo.id,
            conteudo=conteudo_binario
        )
        
        db.session.add(arquivo_conteudo)
        db.session.commit()
        
        # Remover arquivo temporário
        os.remove(caminho_arquivo)
        
        # Formatar resposta
        resultado = {
            'id': novo_arquivo.id,
            'nome': novo_arquivo.nome,
            'tipo': novo_arquivo.tipo,
            'extensao': novo_arquivo.extensao,
            'tamanho': novo_arquivo.tamanho,
            'usuario_id': novo_arquivo.usuario_id,
            'instituicao_id': novo_arquivo.instituicao_id,
            'publico': novo_arquivo.publico,
            'data_upload': novo_arquivo.data_upload.isoformat(),
            'data_atualizacao': novo_arquivo.data_atualizacao.isoformat()
        }
        
        return jsonify(resultado), 201
        
    except Exception as e:
        db.session.rollback()
        # Remover arquivo temporário em caso de erro
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({'error': str(e)}), 500

@files_bp.route('/api/arquivos/<int:arquivo_id>', methods=['DELETE'])
@login_required
def api_excluir_arquivo(arquivo_id):
    """
    API para excluir um arquivo específico.
    """
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    # Verificar se o usuário é o proprietário do arquivo
    if arquivo.usuario_id != current_user.id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Excluir arquivo do banco de dados
        # A exclusão em cascata cuidará do conteúdo do arquivo
        db.session.delete(arquivo)
        db.session.commit()
        
        return jsonify({'message': 'Arquivo excluído com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
