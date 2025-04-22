"""
Formulários para o sistema de classificação de tarefas do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Length
from wtforms.widgets import DateTimeInput
from datetime import datetime

class TarefaForm(FlaskForm):
    """Formulário para criação e edição de tarefas."""
    titulo = StringField('Título', validators=[
        DataRequired(message='Título é obrigatório'),
        Length(min=3, max=255, message='Título deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    classificacao = SelectField('Classificação', choices=[
        ('importancia', 'Importância'),
        ('rotina', 'Rotina'),
        ('urgencia', 'Urgência'),
        ('pausa', 'Pausa')
    ], validators=[DataRequired(message='Classificação é obrigatória')])
    status = SelectField('Status', choices=[
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada')
    ], validators=[DataRequired(message='Status é obrigatório')])
    prioridade = SelectField('Prioridade', choices=[
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ], validators=[DataRequired(message='Prioridade é obrigatória')])
    data_inicio = DateTimeField('Data de Início', format='%Y-%m-%dT%H:%M', 
                               widget=DateTimeInput(), validators=[Optional()])
    data_prazo = DateTimeField('Prazo', format='%Y-%m-%dT%H:%M', 
                              widget=DateTimeInput(), validators=[Optional()])
    responsavel_id = SelectField('Responsável', coerce=int, validators=[Optional()])
    instituicao_id = SelectField('Instituição', coerce=int, validators=[Optional()])
    projeto_id = SelectField('Projeto', coerce=int, validators=[Optional()])
    concluida = BooleanField('Concluída', default=False)
    submit = SubmitField('Salvar Tarefa')

class SubtarefaForm(FlaskForm):
    """Formulário para criação e edição de subtarefas."""
    titulo = StringField('Título', validators=[
        DataRequired(message='Título é obrigatório'),
        Length(min=3, max=255, message='Título deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada')
    ], validators=[DataRequired(message='Status é obrigatório')])
    tarefa_id = HiddenField('ID da Tarefa', validators=[DataRequired()])
    concluida = BooleanField('Concluída', default=False)
    submit = SubmitField('Salvar Subtarefa')

class ComentarioTarefaForm(FlaskForm):
    """Formulário para criação de comentários em tarefas."""
    conteudo = TextAreaField('Comentário', validators=[
        DataRequired(message='Comentário é obrigatório')
    ])
    tarefa_id = HiddenField('ID da Tarefa', validators=[DataRequired()])
    submit = SubmitField('Enviar Comentário')

class ProjetoForm(FlaskForm):
    """Formulário para criação e edição de projetos."""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=255, message='Nome deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    data_inicio = DateTimeField('Data de Início', format='%Y-%m-%dT%H:%M', 
                               widget=DateTimeInput(), validators=[Optional()])
    data_prazo = DateTimeField('Prazo', format='%Y-%m-%dT%H:%M', 
                              widget=DateTimeInput(), validators=[Optional()])
    status = SelectField('Status', choices=[
        ('ativo', 'Ativo'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('suspenso', 'Suspenso')
    ], validators=[DataRequired(message='Status é obrigatório')])
    instituicao_id = SelectField('Instituição', coerce=int, validators=[Optional()])
    submit = SubmitField('Salvar Projeto')

class InstituicaoForm(FlaskForm):
    """Formulário para criação e edição de instituições."""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=255, message='Nome deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    endereco = StringField('Endereço', validators=[Optional()])
    telefone = StringField('Telefone', validators=[Optional()])
    email = StringField('Email', validators=[Optional()])
    site = StringField('Site', validators=[Optional()])
    submit = SubmitField('Salvar Instituição')

class EventoCalendarioForm(FlaskForm):
    """Formulário para criação e edição de eventos do calendário."""
    titulo = StringField('Título', validators=[
        DataRequired(message='Título é obrigatório'),
        Length(min=3, max=255, message='Título deve ter entre 3 e 255 caracteres')
    ])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    data_inicio = DateTimeField('Data de Início', format='%Y-%m-%dT%H:%M', 
                               widget=DateTimeInput(), validators=[DataRequired()])
    data_fim = DateTimeField('Data de Término', format='%Y-%m-%dT%H:%M', 
                            widget=DateTimeInput(), validators=[DataRequired()])
    dia_todo = BooleanField('Dia Todo', default=False)
    cor = StringField('Cor', default="#0d6efd", validators=[Optional()])
    tarefa_id = SelectField('Tarefa Relacionada', coerce=int, validators=[Optional()])
    submit = SubmitField('Salvar Evento')

class FiltroTarefasForm(FlaskForm):
    """Formulário para filtrar tarefas."""
    classificacao = SelectField('Classificação', choices=[
        ('', 'Todas'),
        ('importancia', 'Importância'),
        ('rotina', 'Rotina'),
        ('urgencia', 'Urgência'),
        ('pausa', 'Pausa')
    ], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'Todos'),
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada')
    ], validators=[Optional()])
    prioridade = SelectField('Prioridade', choices=[
        ('', 'Todas'),
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ], validators=[Optional()])
    responsavel_id = SelectField('Responsável', coerce=int, validators=[Optional()])
    instituicao_id = SelectField('Instituição', coerce=int, validators=[Optional()])
    projeto_id = SelectField('Projeto', coerce=int, validators=[Optional()])
    termo = StringField('Termo de Pesquisa', validators=[Optional()])
    submit = SubmitField('Filtrar')
