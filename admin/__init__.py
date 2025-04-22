"""
Módulo de inicialização do dashboard administrativo
Serra Projetos Educacionais
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Importar extensões da aplicação
from auth import db

def init_app(app):
    """
    Inicializa o módulo de dashboard administrativo na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Registrar blueprint
    from .admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Criar tabelas no banco de dados (em ambiente de desenvolvimento)
    if app.config.get('ENV') == 'development':
        with app.app_context():
            from .admin_models import Base
            Base.metadata.create_all(db.engine)
    
    return app
