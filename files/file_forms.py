"""
Formulários para o sistema de gerenciamento de arquivos do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, BooleanField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

class UploadArquivoForm(FlaskForm):
    """Formulário para upload de arquivos."""
    arquivo = FileField('Arquivo', validators=[
        FileRequired(message='Selecione um arquivo para upload'),
        FileAllowed(['pdf', 'doc', 'docx', 'txt'], 'Apenas arquivos PDF, DOC, DOCX e TXT são permitidos')
    ])
    instituicao_id = SelectField('Instituição', coerce=int, validators=[Optional()])
    publico = BooleanField('Arquivo público', default=False)
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Enviar Arquivo')

class PesquisaArquivoForm(FlaskForm):
    """Formulário para pesquisa de arquivos."""
    termo = StringField('Termo de pesquisa', validators=[Optional()])
    tipo = SelectField('Tipo de arquivo', choices=[
        ('', 'Todos'),
        ('pdf', 'PDF'),
        ('doc', 'Word'),
        ('txt', 'Texto')
    ], validators=[Optional()])
    submit = SubmitField('Pesquisar')
