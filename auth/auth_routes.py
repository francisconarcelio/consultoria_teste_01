"""
Rotas de autenticação para o Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets
import json
import os
import re
import logging
from functools import wraps

# Importar modelos e configurações
from .auth_models import Usuario, PerfilUsuario, AutenticacaoExterna, LogAutenticacao, ConsentimentoLGPD
from .auth_utils import enviar_email_recuperacao, validar_senha, validar_email, gerar_token_jwt, verificar_token_jwt
from .auth_forms import LoginForm, RegistroForm, RecuperacaoSenhaForm, RedefinirSenhaForm

# Configuração do Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Configuração de logging
logger = logging.getLogger(__name__)

# Decorador para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash('Acesso negado. Você precisa ser um administrador para acessar esta página.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota para página de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver autenticado, redirecionar para a página inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Obter dados do formulário
        email = form.email.data
        senha = form.senha.data
        lembrar = form.lembrar.data
        
        # Buscar usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificar se o usuário existe e a senha está correta
        if usuario and usuario.verificar_senha(senha):
            # Verificar se o usuário está ativo
            if usuario.status != 'ativo':
                flash('Sua conta está inativa ou bloqueada. Entre em contato com o suporte.', 'danger')
                return render_template('auth/login.html', form=form)
            
            # Resetar tentativas de login
            usuario.resetar_tentativas_login()
            
            # Atualizar último login
            usuario.ultimo_login = datetime.now()
            
            # Registrar log de autenticação
            log = LogAutenticacao(
                usuario_id=usuario.id,
                email=usuario.email,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
                acao='login_sucesso'
            )
            
            # Salvar alterações no banco de dados
            db.session.add(log)
            db.session.commit()
            
            # Fazer login do usuário
            login_user(usuario, remember=lembrar)
            
            # Redirecionar para a página solicitada ou para o dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            return redirect(next_page)
        else:
            # Incrementar tentativas de login se o usuário existir
            if usuario:
                tentativas = usuario.incrementar_tentativas_login()
                
                # Bloquear usuário após 5 tentativas
                if tentativas >= 5:
                    usuario.status = 'bloqueado'
                    
                    # Registrar log de bloqueio
                    log = LogAutenticacao(
                        usuario_id=usuario.id,
                        email=usuario.email,
                        ip=request.remote_addr,
                        user_agent=request.user_agent.string,
                        acao='bloqueio',
                        detalhes='Bloqueio automático após 5 tentativas de login'
                    )
                    db.session.add(log)
                
                db.session.commit()
            
            # Registrar log de falha de autenticação
            log = LogAutenticacao(
                usuario_id=usuario.id if usuario else None,
                email=email,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
                acao='login_falha'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Email ou senha incorretos. Por favor, tente novamente.', 'danger')
    
    return render_template('auth/login.html', form=form)

# Rota para logout
@auth_bp.route('/logout')
@login_required
def logout():
    # Registrar log de logout
    log = LogAutenticacao(
        usuario_id=current_user.id,
        email=current_user.email,
        ip=request.remote_addr,
        user_agent=request.user_agent.string,
        acao='logout'
    )
    db.session.add(log)
    db.session.commit()
    
    # Fazer logout do usuário
    logout_user()
    
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('auth.login'))

# Rota para registro de novo usuário
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # Se o usuário já estiver autenticado, redirecionar para a página inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistroForm()
    
    if form.validate_on_submit():
        try:
            # Obter dados do formulário
            nome_completo = form.nome_completo.data
            email = form.email.data
            username = form.username.data
            senha = form.senha.data
            
            # Validar formato de email
            if not validar_email(email):
                flash('O email fornecido não é válido.', 'danger')
                return render_template('auth/registro.html', form=form)
            
            # Validar força da senha
            if not validar_senha(senha):
                flash('A senha deve ter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais.', 'danger')
                return render_template('auth/registro.html', form=form)
            
            # Gerar salt e hash da senha
            salt = Usuario.gerar_salt()
            senha_hash = Usuario.hash_senha(senha, salt)
            
            # Criar novo usuário
            novo_usuario = Usuario(
                nome_completo=nome_completo,
                email=email,
                username=username,
                senha_hash=senha_hash,
                salt=salt,
                tipo='cliente',  # Tipo padrão para novos registros
                status='pendente'  # Status inicial pendente até confirmação
            )
            
            # Criar perfil vazio para o usuário
            perfil = PerfilUsuario(usuario=novo_usuario)
            
            # Adicionar ao banco de dados
            db.session.add(novo_usuario)
            db.session.add(perfil)
            db.session.commit()
            
            # Criar consentimento LGPD inicial
            consentimento = ConsentimentoLGPD(
                usuario_id=novo_usuario.id,
                tipo_consentimento='termos_uso',
                texto_consentimento='Termos de uso da plataforma Serra Projetos Educacionais',
                versao='1.0',
                consentimento_dado=True,
                data_consentimento=datetime.now(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            # Adicionar consentimento de política de privacidade
            consentimento_privacidade = ConsentimentoLGPD(
                usuario_id=novo_usuario.id,
                tipo_consentimento='politica_privacidade',
                texto_consentimento='Política de privacidade da plataforma Serra Projetos Educacionais',
                versao='1.0',
                consentimento_dado=True,
                data_consentimento=datetime.now(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            db.session.add(consentimento)
            db.session.add(consentimento_privacidade)
            db.session.commit()
            
            # Enviar email de confirmação (implementação futura)
            # enviar_email_confirmacao(novo_usuario)
            
            flash('Registro realizado com sucesso! Por favor, aguarde a aprovação do administrador para acessar o sistema.', 'success')
            return redirect(url_for('auth.login'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Email ou nome de usuário já cadastrado. Por favor, tente outro.', 'danger')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro no registro: {str(e)}")
            flash('Ocorreu um erro durante o registro. Por favor, tente novamente.', 'danger')
    
    return render_template('auth/registro.html', form=form)

# Rota para solicitação de recuperação de senha
@auth_bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    # Se o usuário já estiver autenticado, redirecionar para a página inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RecuperacaoSenhaForm()
    
    if form.validate_on_submit():
        email = form.email.data
        
        # Buscar usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Mesmo que o usuário não exista, mostrar a mesma mensagem para evitar enumeração de usuários
        if usuario:
            # Gerar token de recuperação
            token = usuario.gerar_token_recuperacao()
            
            # Registrar log de solicitação de recuperação
            log = LogAutenticacao(
                usuario_id=usuario.id,
                email=usuario.email,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
                acao='recuperacao_senha'
            )
            db.session.add(log)
            db.session.commit()
            
            # Enviar email com link de recuperação
            try:
                enviar_email_recuperacao(usuario, token)
            except Exception as e:
                logger.error(f"Erro ao enviar email de recuperação: {str(e)}")
                # Continuar mesmo com erro no envio de email
        
        flash('Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_senha.html', form=form)

# Rota para redefinição de senha
@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Se o usuário já estiver autenticado, redirecionar para a página inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Buscar usuário pelo token de recuperação
    usuario = Usuario.query.filter_by(token_recuperacao=token).first()
    
    # Verificar se o token é válido
    if not usuario or not usuario.verificar_token_recuperacao(token):
        flash('O link de recuperação é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.recuperar_senha'))
    
    form = RedefinirSenhaForm()
    
    if form.validate_on_submit():
        # Obter nova senha
        nova_senha = form.senha.data
        
        # Validar força da senha
        if not validar_senha(nova_senha):
            flash('A senha deve ter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais.', 'danger')
            return render_template('auth/redefinir_senha.html', form=form, token=token)
        
        # Gerar novo salt e hash da senha
        salt = Usuario.gerar_salt()
        senha_hash = Usuario.hash_senha(nova_senha, salt)
        
        # Atualizar senha do usuário
        usuario.senha_hash = senha_hash
        usuario.salt = salt
        usuario.token_recuperacao = None
        usuario.expiracao_token = None
        usuario.status = 'ativo'  # Ativar usuário se estiver bloqueado por tentativas de login
        usuario.tentativas_login = 0
        
        # Registrar log de alteração de senha
        log = LogAutenticacao(
            usuario_id=usuario.id,
            email=usuario.email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='alteracao_senha'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Sua senha foi redefinida com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/redefinir_senha.html', form=form, token=token)

# Rota para autenticação via Google
@auth_bp.route('/auth/google')
def auth_google():
    # Implementação da autenticação via Google OAuth2
    # Redirecionar para a página de autenticação do Google
    redirect_uri = url_for('auth.callback_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# Rota de callback para autenticação via Google
@auth_bp.route('/auth/google/callback')
def callback_google():
    # Processar resposta da autenticação do Google
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)
    
    # Verificar se o usuário já existe
    auth_externa = AutenticacaoExterna.query.filter_by(
        provedor='google',
        provedor_id=user_info['sub']
    ).first()
    
    if auth_externa:
        # Usuário já existe, fazer login
        usuario = auth_externa.usuario
        
        # Verificar se o usuário está ativo
        if usuario.status != 'ativo':
            flash('Sua conta está inativa ou bloqueada. Entre em contato com o suporte.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Atualizar último login
        usuario.ultimo_login = datetime.now()
        
        # Registrar log de autenticação
        log = LogAutenticacao(
            usuario_id=usuario.id,
            email=usuario.email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='login_sucesso',
            detalhes='Login via Google'
        )
        
        # Atualizar token
        auth_externa.token = json.dumps(token)
        auth_externa.data_atualizacao = datetime.now()
        
        db.session.add(log)
        db.session.commit()
        
        # Fazer login do usuário
        login_user(usuario)
        
        return redirect(url_for('main.dashboard'))
    else:
        # Novo usuário, criar conta
        try:
            # Criar novo usuário
            novo_usuario = Usuario(
                nome_completo=user_info.get('name', ''),
                email=user_info.get('email', ''),
                username=user_info.get('email', '').split('@')[0],
                senha_hash='',  # Sem senha para login externo
                salt='',
                tipo='cliente',
                status='ativo'  # Ativo imediatamente para login externo
            )
            
            # Criar perfil para o usuário
            perfil = PerfilUsuario(
                usuario=novo_usuario,
                foto_perfil=user_info.get('picture', '')
            )
            
            # Adicionar ao banco de dados
            db.session.add(novo_usuario)
            db.session.add(perfil)
            db.session.flush()  # Para obter o ID do usuário
            
            # Criar registro de autenticação externa
            auth_externa = AutenticacaoExterna(
                usuario_id=novo_usuario.id,
                provedor='google',
                provedor_id=user_info['sub'],
                email=user_info.get('email', ''),
                token=json.dumps(token)
            )
            
            # Criar consentimentos LGPD
            consentimento = ConsentimentoLGPD(
                usuario_id=novo_usuario.id,
                tipo_consentimento='termos_uso',
                texto_consentimento='Termos de uso da plataforma Serra Projetos Educacionais',
                versao='1.0',
                consentimento_dado=True,
                data_consentimento=datetime.now(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            consentimento_privacidade = ConsentimentoLGPD(
                usuario_id=novo_usuario.id,
                tipo_consentimento='politica_privacidade',
                texto_consentimento='Política de privacidade da plataforma Serra Projetos Educacionais',
                versao='1.0',
                consentimento_dado=True,
                data_consentimento=datetime.now(),
                ip=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            db.session.add(auth_externa)
            db.session.add(consentimento)
            db.session.add(consentimento_privacidade)
            
            # Registrar log de criação de conta
            log = LogAutenticacao(
                usuario_id=novo_usuario.id,
                email=novo_usuario.email,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
                acao='login_sucesso',
                detalhes='Criação de conta via Google'
            )
            db.session.add(log)
            
            db.session.commit()
            
            # Fazer login do usuário
            login_user(novo_usuario)
            
            flash('Conta criada com sucesso via Google!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao criar conta. Email já cadastrado.', 'danger')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro na autenticação Google: {str(e)}")
            flash('Ocorreu um erro durante a autenticação. Por favor, tente novamente.', 'danger')
            return redirect(url_for('auth.login'))

# Rotas similares para Apple e Microsoft (implementação futura)
@auth_bp.route('/auth/apple')
def auth_apple():
    # Placeholder para autenticação via Apple
    flash('Autenticação via Apple será implementada em breve.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/auth/microsoft')
def auth_microsoft():
    # Placeholder para autenticação via Microsoft
    flash('Autenticação via Microsoft será implementada em breve.', 'info')
    return redirect(url_for('auth.login'))

# Rota para painel de administração de usuários (apenas para administradores)
@auth_bp.route('/admin/usuarios')
@login_required
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.all()
    return render_template('auth/admin_usuarios.html', usuarios=usuarios)

# Rota para ativar/desativar usuário (apenas para administradores)
@auth_bp.route('/admin/usuarios/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def alterar_status_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir alterar o próprio status
    if usuario.id == current_user.id:
        flash('Você não pode alterar seu próprio status.', 'danger')
        return redirect(url_for('auth.admin_usuarios'))
    
    novo_status = request.form.get('status')
    if novo_status in ['ativo', 'inativo', 'bloqueado', 'pendente']:
        usuario.status = novo_status
        
        # Registrar log de alteração de status
        log = LogAutenticacao(
            usuario_id=usuario.id,
            email=usuario.email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='alteracao_status',
            detalhes=f'Status alterado para {novo_status} por {current_user.nome_completo}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Status do usuário alterado para {novo_status}.', 'success')
    else:
        flash('Status inválido.', 'danger')
    
    return redirect(url_for('auth.admin_usuarios'))

# Rota para alterar tipo de usuário (apenas para administradores)
@auth_bp.route('/admin/usuarios/<int:id>/tipo', methods=['POST'])
@login_required
@admin_required
def alterar_tipo_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir alterar o próprio tipo
    if usuario.id == current_user.id:
        flash('Você não pode alterar seu próprio tipo.', 'danger')
        return redirect(url_for('auth.admin_usuarios'))
    
    novo_tipo = request.form.get('tipo')
    if novo_tipo in ['admin', 'consultor', 'gestor', 'cliente']:
        usuario.tipo = novo_tipo
        
        # Registrar log de alteração de tipo
        log = LogAutenticacao(
            usuario_id=usuario.id,
            email=usuario.email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='alteracao_tipo',
            detalhes=f'Tipo alterado para {novo_tipo} por {current_user.nome_completo}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Tipo do usuário alterado para {novo_tipo}.', 'success')
    else:
        flash('Tipo inválido.', 'danger')
    
    return redirect(url_for('auth.admin_usuarios'))

# Rota para perfil do usuário
@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        try:
            # Atualizar informações do perfil
            current_user.nome_completo = request.form.get('nome_completo')
            
            # Atualizar perfil
            if not current_user.perfil:
                current_user.perfil = PerfilUsuario(usuario_id=current_user.id)
            
            current_user.perfil.telefone = request.form.get('telefone')
            current_user.perfil.cargo = request.form.get('cargo')
            current_user.perfil.departamento = request.form.get('departamento')
            current_user.perfil.bio = request.form.get('bio')
            
            # Processar foto de perfil (implementação futura)
            
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar perfil: {str(e)}")
            flash('Ocorreu um erro ao atualizar o perfil.', 'danger')
    
    return render_template('auth/perfil.html', usuario=current_user)

# Rota para alterar senha
@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        # Verificar se a senha atual está correta
        if not current_user.verificar_senha(senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('auth/alterar_senha.html')
        
        # Verificar se as novas senhas coincidem
        if nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem.', 'danger')
            return render_template('auth/alterar_senha.html')
        
        # Validar força da nova senha
        if not validar_senha(nova_senha):
            flash('A nova senha deve ter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais.', 'danger')
            return render_template('auth/alterar_senha.html')
        
        try:
            # Gerar novo salt e hash da senha
            salt = Usuario.gerar_salt()
            senha_hash = Usuario.hash_senha(nova_senha, salt)
            
            # Atualizar senha do usuário
            current_user.senha_hash = senha_hash
            current_user.salt = salt
            
            # Registrar log de alteração de senha
            log = LogAutenticacao(
                usuario_id=current_user.id,
                email=current_user.email,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
                acao='alteracao_senha'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao alterar senha: {str(e)}")
            flash('Ocorreu um erro ao alterar a senha.', 'danger')
    
    return render_template('auth/alterar_senha.html')

# Rota para gerenciar consentimentos LGPD
@auth_bp.route('/consentimentos', methods=['GET', 'POST'])
@login_required
def consentimentos():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        consentimento_dado = request.form.get('consentimento') == 'on'
        
        # Buscar consentimento existente
        consentimento = ConsentimentoLGPD.query.filter_by(
            usuario_id=current_user.id,
            tipo_consentimento=tipo
        ).first()
        
        if consentimento:
            # Atualizar consentimento existente
            consentimento.consentimento_dado = consentimento_dado
            consentimento.data_consentimento = datetime.now() if consentimento_dado else None
            consentimento.ip = request.remote_addr if consentimento_dado else None
            consentimento.user_agent = request.user_agent.string if consentimento_dado else None
        else:
            # Criar novo consentimento
            versao = '1.0'  # Obter versão atual das configurações
            texto = 'Termos de uso' if tipo == 'termos_uso' else 'Política de privacidade'
            
            consentimento = ConsentimentoLGPD(
                usuario_id=current_user.id,
                tipo_consentimento=tipo,
                texto_consentimento=texto,
                versao=versao,
                consentimento_dado=consentimento_dado,
                data_consentimento=datetime.now() if consentimento_dado else None,
                ip=request.remote_addr if consentimento_dado else None,
                user_agent=request.user_agent.string if consentimento_dado else None
            )
            db.session.add(consentimento)
        
        db.session.commit()
        flash('Preferências de consentimento atualizadas com sucesso!', 'success')
    
    # Buscar consentimentos do usuário
    consentimentos = ConsentimentoLGPD.query.filter_by(usuario_id=current_user.id).all()
    
    return render_template('auth/consentimentos.html', consentimentos=consentimentos)

# Rota para API de autenticação (JWT)
@auth_bp.route('/api/token', methods=['POST'])
def api_token():
    data = request.get_json()
    
    if not data or 'email' not in data or 'senha' not in data:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    email = data.get('email')
    senha = data.get('senha')
    
    # Buscar usuário pelo email
    usuario = Usuario.query.filter_by(email=email).first()
    
    # Verificar se o usuário existe e a senha está correta
    if usuario and usuario.verificar_senha(senha):
        # Verificar se o usuário está ativo
        if usuario.status != 'ativo':
            return jsonify({'error': 'Conta inativa ou bloqueada'}), 403
        
        # Resetar tentativas de login
        usuario.resetar_tentativas_login()
        
        # Atualizar último login
        usuario.ultimo_login = datetime.now()
        
        # Registrar log de autenticação
        log = LogAutenticacao(
            usuario_id=usuario.id,
            email=usuario.email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='login_sucesso',
            detalhes='Login via API'
        )
        db.session.add(log)
        db.session.commit()
        
        # Gerar token JWT
        token = gerar_token_jwt(usuario)
        
        return jsonify({
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': usuario.id,
                'nome': usuario.nome_completo,
                'email': usuario.email,
                'tipo': usuario.tipo
            }
        })
    else:
        # Incrementar tentativas de login se o usuário existir
        if usuario:
            tentativas = usuario.incrementar_tentativas_login()
            
            # Bloquear usuário após 5 tentativas
            if tentativas >= 5:
                usuario.status = 'bloqueado'
                
                # Registrar log de bloqueio
                log = LogAutenticacao(
                    usuario_id=usuario.id,
                    email=usuario.email,
                    ip=request.remote_addr,
                    user_agent=request.user_agent.string,
                    acao='bloqueio',
                    detalhes='Bloqueio automático após 5 tentativas de login via API'
                )
                db.session.add(log)
            
            db.session.commit()
        
        # Registrar log de falha de autenticação
        log = LogAutenticacao(
            usuario_id=usuario.id if usuario else None,
            email=email,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            acao='login_falha',
            detalhes='Falha de login via API'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'error': 'Credenciais inválidas'}), 401

# Rota para verificar token JWT
@auth_bp.route('/api/verify-token', methods=['POST'])
def api_verify_token():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token não fornecido'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Verificar token
    payload = verificar_token_jwt(token)
    
    if not payload:
        return jsonify({'error': 'Token inválido ou expirado'}), 401
    
    # Buscar usuário pelo ID no payload
    usuario = Usuario.query.get(payload.get('sub'))
    
    if not usuario or usuario.status != 'ativo':
        return jsonify({'error': 'Usuário inativo ou não encontrado'}), 403
    
    return jsonify({
        'valid': True,
        'user': {
            'id': usuario.id,
            'nome': usuario.nome_completo,
            'email': usuario.email,
            'tipo': usuario.tipo
        }
    })
