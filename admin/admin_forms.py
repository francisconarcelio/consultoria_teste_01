"""
Formulários para o dashboard administrativo do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, BooleanField, SubmitField, HiddenField
from wtforms import IntegerField, PasswordField, EmailField, MultipleFileField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Length, Email, EqualTo, ValidationError
from wtforms.widgets import DateTimeInput
from datetime import datetime

class ConfiguracaoForm(FlaskForm):
    """Formulário para edição de configurações do sistema."""
    chave = StringField('Chave', validators=[
        DataRequired(message='Chave é obrigatória'),
        Length(min=3, max=100, message='Chave deve ter entre 3 e 100 caracteres')
    ])
    valor = TextAreaField('Valor', validators=[Optional()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    tipo = SelectField('Tipo', choices=[
        ('string', 'Texto'),
        ('integer', 'Número Inteiro'),
        ('boolean', 'Booleano'),
        ('json', 'JSON')
    ], validators=[DataRequired(message='Tipo é obrigatório')])
    categoria = SelectField('Categoria', choices=[
        ('sistema', 'Sistema'),
        ('email', 'Email'),
        ('seguranca', 'Segurança'),
        ('integracao', 'Integração')
    ], validators=[DataRequired(message='Categoria é obrigatória')])
    submit = SubmitField('Salvar Configuração')

class FiltroLogsForm(FlaskForm):
    """Formulário para filtrar logs do sistema."""
    tipo = SelectField('Tipo', choices=[
        ('', 'Todos'),
        ('acesso', 'Acesso'),
        ('erro', 'Erro'),
        ('acao', 'Ação'),
        ('seguranca', 'Segurança')
    ], validators=[Optional()])
    nivel = SelectField('Nível', choices=[
        ('', 'Todos'),
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('critical', 'Crítico')
    ], validators=[Optional()])
    usuario_id = SelectField('Usuário', coerce=int, validators=[Optional()])
    data_inicio = DateTimeField('Data Início', format='%Y-%m-%dT%H:%M', 
                               widget=DateTimeInput(), validators=[Optional()])
    data_fim = DateTimeField('Data Fim', format='%Y-%m-%dT%H:%M', 
                            widget=DateTimeInput(), validators=[Optional()])
    termo = StringField('Termo de Pesquisa', validators=[Optional()])
    submit = SubmitField('Filtrar')

class BackupForm(FlaskForm):
    """Formulário para criação de backup do sistema."""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=255, message='Nome deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    tipo = SelectField('Tipo', choices=[
        ('completo', 'Completo'),
        ('parcial', 'Parcial')
    ], validators=[DataRequired(message='Tipo é obrigatório')])
    incluir_arquivos = BooleanField('Incluir Arquivos', default=True)
    submit = SubmitField('Criar Backup')

class RestaurarBackupForm(FlaskForm):
    """Formulário para restauração de backup do sistema."""
    backup_id = SelectField('Backup', coerce=int, validators=[
        DataRequired(message='Backup é obrigatório')
    ])
    confirmar = BooleanField('Confirmo que entendo que esta ação substituirá os dados atuais', validators=[
        DataRequired(message='Você deve confirmar esta ação')
    ])
    submit = SubmitField('Restaurar Backup')

class RelatorioForm(FlaskForm):
    """Formulário para geração de relatórios."""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=255, message='Nome deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    tipo = SelectField('Tipo', choices=[
        ('usuarios', 'Usuários'),
        ('tarefas', 'Tarefas'),
        ('arquivos', 'Arquivos'),
        ('atividades', 'Atividades')
    ], validators=[DataRequired(message='Tipo é obrigatório')])
    formato = SelectField('Formato', choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ], validators=[DataRequired(message='Formato é obrigatório')])
    periodo_inicio = DateTimeField('Período Início', format='%Y-%m-%dT%H:%M', 
                                  widget=DateTimeInput(), validators=[Optional()])
    periodo_fim = DateTimeField('Período Fim', format='%Y-%m-%dT%H:%M', 
                               widget=DateTimeInput(), validators=[Optional()])
    agendar = BooleanField('Agendar Relatório', default=False)
    frequencia = SelectField('Frequência', choices=[
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('sob_demanda', 'Sob Demanda')
    ], validators=[Optional()])
    destinatarios = TextAreaField('Destinatários (emails separados por vírgula)', validators=[Optional()])
    submit = SubmitField('Gerar Relatório')

class GerenciarUsuarioForm(FlaskForm):
    """Formulário para gerenciamento de usuários."""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    sobrenome = StringField('Sobrenome', validators=[
        DataRequired(message='Sobrenome é obrigatório'),
        Length(min=2, max=100, message='Sobrenome deve ter entre 2 e 100 caracteres')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    perfil = SelectField('Perfil', choices=[
        ('admin', 'Administrador'),
        ('gestor', 'Gestor'),
        ('consultor', 'Consultor'),
        ('cliente', 'Cliente')
    ], validators=[DataRequired(message='Perfil é obrigatório')])
    ativo = BooleanField('Ativo', default=True)
    redefinir_senha = BooleanField('Enviar Email para Redefinição de Senha', default=False)
    submit = SubmitField('Salvar Usuário')

class NotificacaoSistemaForm(FlaskForm):
    """Formulário para envio de notificações do sistema."""
    titulo = StringField('Título', validators=[
        DataRequired(message='Título é obrigatório'),
        Length(min=3, max=255, message='Título deve ter entre 3 e 255 caracteres')
    ])
    mensagem = TextAreaField('Mensagem', validators=[
        DataRequired(message='Mensagem é obrigatória')
    ])
    tipo = SelectField('Tipo', choices=[
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('success', 'Sucesso'),
        ('error', 'Erro')
    ], validators=[DataRequired(message='Tipo é obrigatório')])
    destinatarios = SelectField('Destinatários', choices=[
        ('todos', 'Todos os Usuários'),
        ('admins', 'Administradores'),
        ('gestores', 'Gestores'),
        ('consultores', 'Consultores'),
        ('clientes', 'Clientes'),
        ('especifico', 'Usuário Específico')
    ], validators=[DataRequired(message='Destinatários é obrigatório')])
    usuario_id = SelectField('Usuário Específico', coerce=int, validators=[Optional()])
    link = StringField('Link (opcional)', validators=[Optional()])
    submit = SubmitField('Enviar Notificação')
