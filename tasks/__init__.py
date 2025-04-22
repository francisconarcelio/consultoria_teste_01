"""
Módulo de inicialização do sistema de classificação de tarefas
Serra Projetos Educacionais
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Importar extensões da aplicação
from auth import db

def init_app(app):
    """
    Inicializa o módulo de gerenciamento de tarefas na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Registrar blueprint
    from .task_routes import tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    # Criar tabelas no banco de dados (em ambiente de desenvolvimento)
    if app.config.get('ENV') == 'development':
        with app.app_context():
            from .task_models import Base
            Base.metadata.create_all(db.engine)
    
    return app
