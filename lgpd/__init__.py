"""
Módulo de conformidade com a LGPD (Lei Geral de Proteção de Dados)
Serra Projetos Educacionais
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func
from datetime import datetime, timedelta
import json
import os
import hashlib
import secrets
from werkzeug.utils import secure_filename

# Importar modelos e configurações
from auth.auth_models import Usuario, ConsentimentoLGPD
from admin.admin_models import LogSistema

# Importar extensões da aplicação
from auth import db

# Configuração do Blueprint
lgpd_bp = Blueprint('lgpd', __name__, template_folder='templates')

# Rotas para políticas de privacidade e termos de uso
@lgpd_bp.route('/privacy-policy')
def privacy_policy():
    """
    Página de política de privacidade.
    """
    return render_template('lgpd/privacy_policy.html')

@lgpd_bp.route('/terms')
def terms():
    """
    Página de termos de uso.
    """
    return render_template('lgpd/terms.html')

# Rota para gerenciamento de consentimentos
@lgpd_bp.route('/consent', methods=['GET', 'POST'])
@login_required
def manage_consent():
    """
    Página para gerenciamento de consentimentos do usuário.
    """
    # Obter consentimentos atuais do usuário
    consentimentos = ConsentimentoLGPD.query.filter_by(usuario_id=current_user.id).all()
    
    if request.method == 'POST':
        try:
            # Atualizar consentimentos
            for tipo_consentimento in ['dados_pessoais', 'comunicacoes', 'cookies', 'compartilhamento']:
                consentido = request.form.get(tipo_consentimento) == 'on'
                
                # Verificar se já existe consentimento deste tipo
                consentimento = ConsentimentoLGPD.query.filter_by(
                    usuario_id=current_user.id,
                    tipo=tipo_consentimento
                ).first()
                
                if consentimento:
                    # Atualizar consentimento existente
                    consentimento.consentido = consentido
                    consentimento.data_atualizacao = datetime.now()
                else:
                    # Criar novo consentimento
                    consentimento = ConsentimentoLGPD(
                        usuario_id=current_user.id,
                        tipo=tipo_consentimento,
                        consentido=consentido
                    )
                    db.session.add(consentimento)
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Consentimentos LGPD atualizados pelo usuário {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Suas preferências de privacidade foram atualizadas com sucesso.', 'success')
            return redirect(url_for('lgpd.manage_consent'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar preferências de privacidade: {str(e)}', 'danger')
    
    # Converter consentimentos para dicionário para facilitar acesso no template
    consentimentos_dict = {c.tipo: c.consentido for c in consentimentos}
    
    return render_template(
        'lgpd/manage_consent.html',
        consentimentos=consentimentos_dict
    )

# Rota para solicitação de exclusão de dados
@lgpd_bp.route('/data-deletion-request', methods=['GET', 'POST'])
@login_required
def data_deletion_request():
    """
    Página para solicitação de exclusão de dados do usuário.
    """
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo', '')
            senha = request.form.get('senha', '')
            
            # Verificar senha
            if not current_user.check_password(senha):
                flash('Senha incorreta. Por favor, tente novamente.', 'danger')
                return redirect(url_for('lgpd.data_deletion_request'))
            
            # Marcar usuário para exclusão
            current_user.exclusao_solicitada = True
            current_user.data_solicitacao_exclusao = datetime.now()
            current_user.motivo_exclusao = motivo
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='warning',
                mensagem=f'Solicitação de exclusão de dados realizada pelo usuário {current_user.email}',
                usuario_id=current_user.id,
                detalhes={'motivo': motivo}
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Sua solicitação de exclusão de dados foi registrada. Entraremos em contato em breve.', 'success')
            return redirect(url_for('auth.logout'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar solicitação de exclusão: {str(e)}', 'danger')
    
    return render_template('lgpd/data_deletion_request.html')

# Rota para download dos dados do usuário
@lgpd_bp.route('/data-export')
@login_required
def data_export():
    """
    Gera e fornece para download um arquivo com todos os dados do usuário.
    """
    try:
        # Coletar dados do usuário
        dados_usuario = {
            'usuario': {
                'id': current_user.id,
                'nome': current_user.nome,
                'sobrenome': current_user.sobrenome,
                'email': current_user.email,
                'data_cadastro': current_user.data_cadastro.isoformat() if current_user.data_cadastro else None,
                'ultimo_acesso': current_user.ultimo_acesso.isoformat() if current_user.ultimo_acesso else None
            },
            'consentimentos': [
                {
                    'tipo': c.tipo,
                    'consentido': c.consentido,
                    'data_consentimento': c.data_consentimento.isoformat() if c.data_consentimento else None,
                    'data_atualizacao': c.data_atualizacao.isoformat() if c.data_atualizacao else None
                }
                for c in ConsentimentoLGPD.query.filter_by(usuario_id=current_user.id).all()
            ],
            'tarefas': [
                {
                    'id': t.id,
                    'titulo': t.titulo,
                    'descricao': t.descricao,
                    'classificacao': t.classificacao.value if t.classificacao else None,
                    'status': t.status.value if t.status else None,
                    'prioridade': t.prioridade.value if t.prioridade else None,
                    'data_criacao': t.data_criacao.isoformat() if t.data_criacao else None,
                    'data_atualizacao': t.data_atualizacao.isoformat() if t.data_atualizacao else None,
                    'data_inicio': t.data_inicio.isoformat() if t.data_inicio else None,
                    'data_prazo': t.data_prazo.isoformat() if t.data_prazo else None,
                    'data_conclusao': t.data_conclusao.isoformat() if t.data_conclusao else None,
                    'concluida': t.concluida
                }
                for t in current_user.tarefas
            ],
            'arquivos': [
                {
                    'id': a.id,
                    'nome': a.nome,
                    'tipo': a.tipo,
                    'tamanho': a.tamanho,
                    'descricao': a.descricao,
                    'data_upload': a.data_upload.isoformat() if a.data_upload else None
                }
                for a in current_user.arquivos
            ]
        }
        
        # Criar diretório temporário para o arquivo
        temp_dir = os.path.join(current_app.instance_path, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Gerar nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"dados_usuario_{current_user.id}_{timestamp}.json"
        filepath = os.path.join(temp_dir, filename)
        
        # Salvar dados em arquivo JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_usuario, f, ensure_ascii=False, indent=4)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='info',
            mensagem=f'Exportação de dados realizada pelo usuário {current_user.email}',
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        # Retornar arquivo para download
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        flash(f'Erro ao exportar dados: {str(e)}', 'danger')
        return redirect(url_for('auth.perfil'))

# Funções de segurança para LGPD
def anonimizar_dados(usuario_id):
    """
    Anonimiza os dados de um usuário após solicitação de exclusão.
    
    Args:
        usuario_id: ID do usuário a ser anonimizado
    """
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return False
        
        # Gerar hash para anonimização
        hash_base = f"{usuario.email}_{secrets.token_hex(16)}"
        hash_anonimo = hashlib.sha256(hash_base.encode()).hexdigest()
        
        # Anonimizar dados pessoais
        usuario.nome = f"Usuário Anonimizado"
        usuario.sobrenome = hash_anonimo[:8]
        usuario.email = f"anonimo_{hash_anonimo[:8]}@example.com"
        usuario.telefone = None
        usuario.endereco = None
        usuario.cidade = None
        usuario.estado = None
        usuario.cep = None
        usuario.pais = None
        usuario.data_nascimento = None
        usuario.genero = None
        usuario.foto_perfil = None
        usuario.biografia = None
        usuario.ativo = False
        usuario.anonimizado = True
        usuario.data_anonimizacao = datetime.now()
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='warning',
            mensagem=f'Dados do usuário ID {usuario_id} foram anonimizados',
            detalhes={'hash_anonimo': hash_anonimo}
        )
        db.session.add(log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao anonimizar dados: {str(e)}")
        return False

def registrar_acesso_dados(usuario_id, tipo_acesso, dados_acessados, ip=None):
    """
    Registra acesso a dados pessoais para fins de auditoria.
    
    Args:
        usuario_id: ID do usuário cujos dados foram acessados
        tipo_acesso: Tipo de acesso (visualização, edição, exclusão)
        dados_acessados: Descrição dos dados acessados
        ip: Endereço IP de quem acessou os dados (opcional)
    """
    try:
        # Registrar log
        log = LogSistema(
            tipo='acesso',
            nivel='info',
            mensagem=f'Acesso a dados pessoais do usuário ID {usuario_id}',
            usuario_id=current_user.id if current_user.is_authenticated else None,
            ip=ip or request.remote_addr,
            detalhes={
                'tipo_acesso': tipo_acesso,
                'dados_acessados': dados_acessados
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar acesso a dados: {str(e)}")
        return False

def verificar_consentimento(usuario_id, tipo_consentimento):
    """
    Verifica se um usuário deu consentimento para determinado tipo de operação.
    
    Args:
        usuario_id: ID do usuário
        tipo_consentimento: Tipo de consentimento a verificar
        
    Returns:
        Boolean indicando se o consentimento foi dado
    """
    consentimento = ConsentimentoLGPD.query.filter_by(
        usuario_id=usuario_id,
        tipo=tipo_consentimento
    ).first()
    
    return consentimento and consentimento.consentido

def criptografar_dado_sensivel(dado):
    """
    Criptografa um dado sensível para armazenamento.
    
    Args:
        dado: Dado a ser criptografado
        
    Returns:
        String com o dado criptografado
    """
    if not dado:
        return None
        
    # Usar chave secreta da aplicação
    chave = current_app.config['SECRET_KEY']
    
    # Gerar salt único
    salt = secrets.token_hex(16)
    
    # Combinar dado com salt e chave
    dado_com_salt = f"{dado}{salt}{chave}"
    
    # Gerar hash
    hash_dado = hashlib.sha256(dado_com_salt.encode()).hexdigest()
    
    # Retornar hash e salt (para poder verificar posteriormente)
    return f"{hash_dado}:{salt}"

def verificar_dado_sensivel(dado, hash_armazenado):
    """
    Verifica se um dado sensível corresponde ao hash armazenado.
    
    Args:
        dado: Dado a ser verificado
        hash_armazenado: Hash armazenado no banco de dados
        
    Returns:
        Boolean indicando se o dado corresponde ao hash
    """
    if not dado or not hash_armazenado:
        return False
        
    # Extrair hash e salt
    partes = hash_armazenado.split(':')
    if len(partes) != 2:
        return False
        
    hash_original, salt = partes
    
    # Usar chave secreta da aplicação
    chave = current_app.config['SECRET_KEY']
    
    # Combinar dado com salt e chave
    dado_com_salt = f"{dado}{salt}{chave}"
    
    # Gerar hash
    hash_verificacao = hashlib.sha256(dado_com_salt.encode()).hexdigest()
    
    # Comparar hashes
    return hash_verificacao == hash_original

# Inicialização do módulo
def init_app(app):
    """
    Inicializa o módulo de LGPD na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Registrar blueprint
    app.register_blueprint(lgpd_bp, url_prefix='/lgpd')
    
    # Adicionar funções ao contexto da aplicação
    app.jinja_env.globals.update(
        verificar_consentimento=verificar_consentimento
    )
    
    # Adicionar middleware para verificação de consentimento
    @app.before_request
    def verificar_consentimentos_necessarios():
        """
        Middleware para verificar se o usuário deu os consentimentos necessários.
        Redireciona para a página de consentimento se necessário.
        """
        # Ignorar para rotas públicas e de autenticação
        if (request.endpoint and (
            request.endpoint.startswith('static') or
            request.endpoint.startswith('auth.') or
            request.endpoint == 'lgpd.privacy_policy' or
            request.endpoint == 'lgpd.terms' or
            request.endpoint == 'lgpd.manage_consent' or
            request.endpoint == 'index'
        )):
            return None
        
        # Verificar se usuário está autenticado
        if current_user.is_authenticated:
            # Verificar se usuário já deu consentimento para dados pessoais
            if not verificar_consentimento(current_user.id, 'dados_pessoais'):
                flash('Por favor, revise e atualize suas preferências de privacidade para continuar.', 'warning')
                return redirect(url_for('lgpd.manage_consent'))
    
    return app

# Importação necessária para send_file
from flask import send_file
