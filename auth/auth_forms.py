"""
Formulários para o sistema de autenticação do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from .auth_utils import validar_email, validar_senha

class LoginForm(FlaskForm):
    """Formulário para login de usuários."""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Formato de email inválido')
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ])
    lembrar = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegistroForm(FlaskForm):
    """Formulário para registro de novos usuários."""
    nome_completo = StringField('Nome Completo', validators=[
        DataRequired(message='Nome completo é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Formato de email inválido')
    ])
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório'),
        Length(min=3, max=50, message='Nome de usuário deve ter entre 3 e 50 caracteres'),
        Regexp('^[A-Za-z0-9_]+$', message='Nome de usuário deve conter apenas letras, números e underscore')
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=8, message='Senha deve ter pelo menos 8 caracteres')
    ])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='As senhas devem ser iguais')
    ])
    aceitar_termos = BooleanField('Eu li e aceito os Termos de Uso e a Política de Privacidade', validators=[
        DataRequired(message='Você deve aceitar os termos para continuar')
    ])
    submit = SubmitField('Registrar')
    
    def validate_senha(self, field):
        """Validação personalizada para verificar a força da senha."""
        if not validar_senha(field.data):
            raise ValidationError('A senha deve conter letras maiúsculas, minúsculas, números e caracteres especiais')

    def validate_email(self, field):
        """Validação personalizada para verificar o formato do email."""
        if not validar_email(field.data):
            raise ValidationError('Formato de email inválido')

class RecuperacaoSenhaForm(FlaskForm):
    """Formulário para solicitação de recuperação de senha."""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Formato de email inválido')
    ])
    submit = SubmitField('Enviar Link de Recuperação')

class RedefinirSenhaForm(FlaskForm):
    """Formulário para redefinição de senha."""
    senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=8, message='Senha deve ter pelo menos 8 caracteres')
    ])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Redefinir Senha')
    
    def validate_senha(self, field):
        """Validação personalizada para verificar a força da senha."""
        if not validar_senha(field.data):
            raise ValidationError('A senha deve conter letras maiúsculas, minúsculas, números e caracteres especiais')

class AlterarSenhaForm(FlaskForm):
    """Formulário para alteração de senha pelo usuário."""
    senha_atual = PasswordField('Senha Atual', validators=[
        DataRequired(message='Senha atual é obrigatória')
    ])
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=8, message='Senha deve ter pelo menos 8 caracteres')
    ])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('nova_senha', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Alterar Senha')
    
    def validate_nova_senha(self, field):
        """Validação personalizada para verificar a força da senha."""
        if not validar_senha(field.data):
            raise ValidationError('A senha deve conter letras maiúsculas, minúsculas, números e caracteres especiais')

class PerfilForm(FlaskForm):
    """Formulário para edição de perfil de usuário."""
    nome_completo = StringField('Nome Completo', validators=[
        DataRequired(message='Nome completo é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    telefone = StringField('Telefone', validators=[
        Length(max=20, message='Telefone deve ter no máximo 20 caracteres')
    ])
    cargo = StringField('Cargo', validators=[
        Length(max=100, message='Cargo deve ter no máximo 100 caracteres')
    ])
    departamento = StringField('Departamento', validators=[
        Length(max=100, message='Departamento deve ter no máximo 100 caracteres')
    ])
    bio = StringField('Biografia', validators=[
        Length(max=500, message='Biografia deve ter no máximo 500 caracteres')
    ])
    submit = SubmitField('Atualizar Perfil')

class ConsentimentoForm(FlaskForm):
    """Formulário para gerenciamento de consentimentos LGPD."""
    termos_uso = BooleanField('Eu aceito os Termos de Uso')
    politica_privacidade = BooleanField('Eu aceito a Política de Privacidade')
    marketing = BooleanField('Eu aceito receber comunicações de marketing')
    submit = SubmitField('Atualizar Preferências')
