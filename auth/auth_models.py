"""
Modelos para o sistema de autenticação do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import datetime
import os
import hashlib
import secrets
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Usuario(Base):
    """Modelo para armazenar informações de usuários do sistema."""
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_completo = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    senha_hash = Column(String(255), nullable=False)
    salt = Column(String(100), nullable=False)
    tipo = Column(Enum('admin', 'consultor', 'gestor', 'cliente', name='tipo_usuario'), default='cliente', nullable=False)
    status = Column(Enum('ativo', 'inativo', 'bloqueado', 'pendente', name='status_usuario'), default='pendente', nullable=False)
    ultimo_login = Column(DateTime, nullable=True)
    tentativas_login = Column(Integer, default=0, nullable=False)
    token_recuperacao = Column(String(100), nullable=True)
    expiracao_token = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    perfil = relationship("PerfilUsuario", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    autenticacoes_externas = relationship("AutenticacaoExterna", back_populates="usuario", cascade="all, delete-orphan")
    logs_autenticacao = relationship("LogAutenticacao", back_populates="usuario")
    tarefas = relationship("Tarefa", back_populates="usuario")
    integracao_calendar = relationship("IntegracaoGoogleCalendar", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    consentimentos = relationship("ConsentimentoLGPD", back_populates="usuario", cascade="all, delete-orphan")
    
    @staticmethod
    def gerar_salt():
        """Gera um salt aleatório para uso na criptografia de senha."""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_senha(senha_texto, salt):
        """Gera um hash seguro da senha utilizando bcrypt."""
        return pwd_context.hash(senha_texto + salt)
    
    def verificar_senha(self, senha_texto):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return pwd_context.verify(senha_texto + self.salt, self.senha_hash)
    
    def gerar_token_recuperacao(self):
        """Gera um token para recuperação de senha e define sua expiração."""
        self.token_recuperacao = secrets.token_urlsafe(64)
        self.expiracao_token = datetime.datetime.now() + datetime.timedelta(hours=24)
        return self.token_recuperacao
    
    def verificar_token_recuperacao(self, token):
        """Verifica se o token de recuperação é válido e não expirou."""
        if self.token_recuperacao != token:
            return False
        if self.expiracao_token is None or self.expiracao_token < datetime.datetime.now():
            return False
        return True
    
    def incrementar_tentativas_login(self):
        """Incrementa o contador de tentativas de login."""
        self.tentativas_login += 1
        return self.tentativas_login
    
    def resetar_tentativas_login(self):
        """Reseta o contador de tentativas de login."""
        self.tentativas_login = 0
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', tipo='{self.tipo}', status='{self.status}')>"


class PerfilUsuario(Base):
    """Modelo para armazenar informações adicionais de perfil do usuário."""
    __tablename__ = 'perfis_usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    telefone = Column(String(20), nullable=True)
    foto_perfil = Column(String(255), nullable=True)
    cargo = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    preferencias = Column(JSON, nullable=True)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="perfil")
    
    def __repr__(self):
        return f"<PerfilUsuario(id={self.id}, usuario_id={self.usuario_id})>"


class AutenticacaoExterna(Base):
    """Modelo para armazenar informações de autenticação via provedores externos."""
    __tablename__ = 'autenticacao_externa'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    provedor = Column(Enum('google', 'apple', 'microsoft', name='provedor_autenticacao'), nullable=False)
    provedor_id = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    token = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="autenticacoes_externas")
    
    __table_args__ = (
        # Garante que a combinação provedor + provedor_id seja única
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<AutenticacaoExterna(id={self.id}, usuario_id={self.usuario_id}, provedor='{self.provedor}')>"


class LogAutenticacao(Base):
    """Modelo para registrar eventos de autenticação no sistema."""
    __tablename__ = 'logs_autenticacao'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    email = Column(String(100), nullable=True)
    ip = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    acao = Column(Enum('login_sucesso', 'login_falha', 'logout', 'recuperacao_senha', 
                        'alteracao_senha', 'bloqueio', name='acao_autenticacao'), nullable=False)
    detalhes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="logs_autenticacao")
    
    def __repr__(self):
        return f"<LogAutenticacao(id={self.id}, usuario_id={self.usuario_id}, acao='{self.acao}')>"


class ConsentimentoLGPD(Base):
    """Modelo para registrar consentimentos LGPD dos usuários."""
    __tablename__ = 'consentimentos_lgpd'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipo_consentimento = Column(String(100), nullable=False)
    texto_consentimento = Column(Text, nullable=False)
    versao = Column(String(20), nullable=False)
    consentimento_dado = Column(Boolean, default=False, nullable=False)
    data_consentimento = Column(DateTime, nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="consentimentos")
    
    def __repr__(self):
        return f"<ConsentimentoLGPD(id={self.id}, usuario_id={self.usuario_id}, tipo='{self.tipo_consentimento}', consentimento_dado={self.consentimento_dado})>"
