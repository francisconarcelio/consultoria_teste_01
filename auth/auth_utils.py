"""
Utilitários para o sistema de autenticação do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

import re
import os
import jwt
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import current_app, url_for

# Configuração de logging
logger = logging.getLogger(__name__)

def validar_email(email):
    """
    Valida o formato de um endereço de email.
    
    Args:
        email: String contendo o endereço de email a ser validado
        
    Returns:
        Boolean indicando se o email é válido
    """
    # Padrão de validação de email
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_senha(senha):
    """
    Valida a força de uma senha.
    
    Args:
        senha: String contendo a senha a ser validada
        
    Returns:
        Boolean indicando se a senha atende aos requisitos mínimos
    """
    # Verificar comprimento mínimo
    if len(senha) < 8:
        return False
    
    # Verificar presença de pelo menos uma letra maiúscula
    if not re.search(r'[A-Z]', senha):
        return False
    
    # Verificar presença de pelo menos uma letra minúscula
    if not re.search(r'[a-z]', senha):
        return False
    
    # Verificar presença de pelo menos um número
    if not re.search(r'[0-9]', senha):
        return False
    
    # Verificar presença de pelo menos um caractere especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False
    
    return True

def enviar_email_recuperacao(usuario, token):
    """
    Envia um email com link para recuperação de senha.
    
    Args:
        usuario: Objeto Usuario para quem o email será enviado
        token: Token de recuperação de senha
        
    Returns:
        Boolean indicando se o email foi enviado com sucesso
    """
    try:
        # Configurações de email (devem ser definidas no arquivo de configuração)
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_user = current_app.config.get('SMTP_USER', 'seu-email@gmail.com')
        smtp_password = current_app.config.get('SMTP_PASSWORD', 'sua-senha')
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = usuario.email
        msg['Subject'] = 'Recuperação de Senha - Serra Projetos Educacionais'
        
        # Link de recuperação
        link = url_for('auth.redefinir_senha', token=token, _external=True)
        
        # Corpo do email
        corpo = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0d6efd; color: white; padding: 10px 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .button {{ display: inline-block; background-color: #0d6efd; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Serra Projetos Educacionais</h2>
                </div>
                <div class="content">
                    <p>Olá, {usuario.nome_completo}!</p>
                    <p>Recebemos uma solicitação para redefinir sua senha. Se você não fez esta solicitação, por favor, ignore este email.</p>
                    <p>Para redefinir sua senha, clique no botão abaixo:</p>
                    <p style="text-align: center;">
                        <a href="{link}" class="button">Redefinir Senha</a>
                    </p>
                    <p>Ou copie e cole o seguinte link no seu navegador:</p>
                    <p>{link}</p>
                    <p>Este link expirará em 24 horas.</p>
                    <p>Atenciosamente,<br>Equipe Serra Projetos Educacionais</p>
                </div>
                <div class="footer">
                    <p>Este é um email automático. Por favor, não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(corpo, 'html'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        
        # Enviar email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de recuperação enviado para {usuario.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar email de recuperação: {str(e)}")
        return False

def enviar_email_confirmacao(usuario):
    """
    Envia um email de confirmação de cadastro.
    
    Args:
        usuario: Objeto Usuario para quem o email será enviado
        
    Returns:
        Boolean indicando se o email foi enviado com sucesso
    """
    # Implementação similar ao enviar_email_recuperacao
    # Será implementado quando necessário
    pass

def gerar_token_jwt(usuario):
    """
    Gera um token JWT para autenticação via API.
    
    Args:
        usuario: Objeto Usuario para quem o token será gerado
        
    Returns:
        String contendo o token JWT
    """
    try:
        # Configurações do token (devem ser definidas no arquivo de configuração)
        secret_key = current_app.config.get('SECRET_KEY', 'chave-secreta-temporaria')
        expiration = current_app.config.get('JWT_EXPIRATION_DELTA', 30)  # minutos
        
        # Criar payload
        payload = {
            'sub': usuario.id,
            'name': usuario.nome_completo,
            'email': usuario.email,
            'role': usuario.tipo,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=expiration)
        }
        
        # Gerar token
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
        
    except Exception as e:
        logger.error(f"Erro ao gerar token JWT: {str(e)}")
        return None

def verificar_token_jwt(token):
    """
    Verifica a validade de um token JWT.
    
    Args:
        token: String contendo o token JWT a ser verificado
        
    Returns:
        Dict contendo o payload do token se válido, None caso contrário
    """
    try:
        # Configurações do token (devem ser definidas no arquivo de configuração)
        secret_key = current_app.config.get('SECRET_KEY', 'chave-secreta-temporaria')
        
        # Decodificar token
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token JWT inválido")
        return None
    except Exception as e:
        logger.error(f"Erro ao verificar token JWT: {str(e)}")
        return None

def registrar_log_seguranca(usuario_id, acao, descricao, ip, user_agent):
    """
    Registra um log de segurança no sistema.
    
    Args:
        usuario_id: ID do usuário relacionado ao log (pode ser None)
        acao: String descrevendo a ação realizada
        descricao: String com detalhes adicionais
        ip: Endereço IP de origem
        user_agent: User-Agent do navegador
        
    Returns:
        Boolean indicando se o log foi registrado com sucesso
    """
    try:
        from .auth_models import LogAutenticacao
        from flask_sqlalchemy import SQLAlchemy
        
        db = SQLAlchemy(current_app)
        
        log = LogAutenticacao(
            usuario_id=usuario_id,
            acao=acao,
            detalhes=descricao,
            ip=ip,
            user_agent=user_agent
        )
        
        db.session.add(log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao registrar log de segurança: {str(e)}")
        return False
