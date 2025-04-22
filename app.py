"""
Arquivo principal da aplicação Flask
Serra Projetos Educacionais - Sistema de Consultoria Educacional
"""

import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(test_config=None):
    """
    Função factory para criar a aplicação Flask.
    
    Args:
        test_config: Configurações para testes (opcional)
        
    Returns:
        Instância da aplicação Flask configurada
    """
    # Criar e configurar a aplicação
    app = Flask(__name__, instance_relative_config=True)
    
    # Configurações padrão
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_insecure'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///serra_consultoria.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10MB
        TEMPLATES_AUTO_RELOAD=True
    )
    
    # Carregar configurações específicas do ambiente
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # Garantir que o diretório de instância existe
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    
    # Inicializar extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configurar login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Registrar blueprints
    from auth import init_app as init_auth
    init_auth(app)
    
    from files import init_app as init_files
    init_files(app)
    
    from tasks import init_app as init_tasks
    init_tasks(app)
    
    from admin import init_app as init_admin
    init_admin(app)
    
    # Integração com Hugging Face
    from huggingface_integration import init_app as init_huggingface
    init_huggingface(app)
    
    # Rota principal
    @app.route('/')
    def index():
        """Rota principal da aplicação."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard principal do usuário."""
        # Obter tarefas do usuário
        tarefas_recentes = Tarefa.query.filter(
            (Tarefa.usuario_id == current_user.id) | 
            (Tarefa.responsavel_id == current_user.id)
        ).order_by(desc(Tarefa.data_criacao)).limit(5).all()
        
        # Obter arquivos recentes
        arquivos_recentes = Arquivo.query.filter_by(
            usuario_id=current_user.id
        ).order_by(desc(Arquivo.data_upload)).limit(5).all()
        
        # Obter notificações não lidas
        notificacoes = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).order_by(desc(Notificacao.data_criacao)).all()
        
        # Obter estatísticas do usuário
        estatisticas = obter_estatisticas_tarefas(current_user.id)
        
        return render_template(
            'dashboard.html',
            tarefas_recentes=tarefas_recentes,
            arquivos_recentes=arquivos_recentes,
            notificacoes=notificacoes,
            estatisticas=estatisticas
        )
    
    # Tratamento de erros
    @app.errorhandler(404)
    def page_not_found(e):
        """Tratamento de erro 404."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Tratamento de erro 500."""
        return render_template('errors/500.html'), 500
    
    # Contexto global para templates
    @app.context_processor
    def utility_processor():
        """Adiciona funções úteis ao contexto dos templates."""
        def format_date(date, format='%d/%m/%Y'):
            """Formata uma data."""
            if date:
                return date.strftime(format)
            return ''
        
        def format_datetime(date, format='%d/%m/%Y %H:%M'):
            """Formata uma data e hora."""
            if date:
                return date.strftime(format)
            return ''
        
        def format_filesize(size):
            """Formata um tamanho de arquivo."""
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        
        return dict(
            format_date=format_date,
            format_datetime=format_datetime,
            format_filesize=format_filesize
        )
    
    return app

# Importações necessárias para o funcionamento da aplicação
from auth.auth_models import Usuario
from tasks.task_models import Tarefa
from tasks.task_utils import obter_estatisticas_tarefas
from files.file_models import Arquivo
from admin.admin_models import Notificacao
from sqlalchemy import desc
from flask_login import login_required

# Função para carregar usuário pelo ID (necessária para o login_manager)
@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário pelo ID."""
    return Usuario.query.get(int(user_id))

# Executar a aplicação se este arquivo for executado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
