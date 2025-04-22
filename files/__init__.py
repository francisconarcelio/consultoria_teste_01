"""
Módulo de inicialização do sistema de gerenciamento de arquivos
Serra Projetos Educacionais
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Importar extensões da aplicação
from auth import db

def init_app(app):
    """
    Inicializa o módulo de gerenciamento de arquivos na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Configurações de upload
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    
    # Registrar blueprint
    from .file_routes import files_bp
    app.register_blueprint(files_bp, url_prefix='/files')
    
    # Criar tabelas no banco de dados (em ambiente de desenvolvimento)
    if app.config.get('ENV') == 'development':
        with app.app_context():
            from .file_models import Base
            Base.metadata.create_all(db.engine)
    
    return app
