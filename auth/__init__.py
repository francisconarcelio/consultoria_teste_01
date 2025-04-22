"""
Módulo de inicialização do sistema de autenticação
Serra Projetos Educacionais
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth

# Inicialização das extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
oauth = OAuth()

def init_app(app):
    """
    Inicializa o módulo de autenticação na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    oauth.init_app(app)
    
    # Configurar login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Configurar provedores OAuth
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID', ''),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET', ''),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    # Importar modelos para que o SQLAlchemy os reconheça
    from .auth_models import Usuario, PerfilUsuario, AutenticacaoExterna, LogAutenticacao, ConsentimentoLGPD
    
    # Configurar user loader para o Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprint
    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Criar tabelas no banco de dados (em ambiente de desenvolvimento)
    if app.config.get('ENV') == 'development':
        with app.app_context():
            db.create_all()
    
    return app
