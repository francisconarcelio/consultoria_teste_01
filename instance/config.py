"""
Arquivo de configuração para integração entre frontend e backend
Serra Projetos Educacionais - Sistema de Consultoria Educacional
"""

import os
from datetime import timedelta

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'chave_segura_para_producao')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = timedelta(days=1)
REMEMBER_COOKIE_DURATION = timedelta(days=14)
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SAMESITE = 'Lax'

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///serra_consultoria.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Configurações de upload
UPLOAD_FOLDER = 'instance/uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# Configurações de email
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@serraprojetos.com.br')

# Configurações do Hugging Face
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
HUGGINGFACE_MODEL = os.environ.get('HUGGINGFACE_MODEL', 'gpt2')

# Configurações do Google
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# Configurações de logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', 'instance/logs/app.log')

# Configurações de backup
BACKUP_DIR = 'instance/backups'
BACKUP_RETENTION_DAYS = 30

# Configurações de relatórios
REPORT_DIR = 'instance/reports'

# Configurações de LGPD
LGPD_CONSENT_REQUIRED = True
LGPD_PRIVACY_POLICY_URL = '/privacy-policy'
LGPD_TERMS_URL = '/terms'
LGPD_DATA_RETENTION_DAYS = 365 * 2  # 2 anos

# Configurações de ambiente
ENV = os.environ.get('FLASK_ENV', 'production')
DEBUG = ENV == 'development'
TESTING = ENV == 'testing'
