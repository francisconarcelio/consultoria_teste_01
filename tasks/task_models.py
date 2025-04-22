"""
Modelos para o sistema de classificação de tarefas do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import datetime
import enum

Base = declarative_base()

class ClassificacaoTarefa(enum.Enum):
    """Enumeração para classificação de tarefas."""
    IMPORTANCIA = "importancia"
    ROTINA = "rotina"
    URGENCIA = "urgencia"
    PAUSA = "pausa"

class StatusTarefa(enum.Enum):
    """Enumeração para status de tarefas."""
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"
    ADIADA = "adiada"

class PrioridadeTarefa(enum.Enum):
    """Enumeração para prioridade de tarefas."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class Tarefa(Base):
    """Modelo para armazenar informações de tarefas no sistema."""
    __tablename__ = 'tarefas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    classificacao = Column(Enum(ClassificacaoTarefa), nullable=False)
    status = Column(Enum(StatusTarefa), default=StatusTarefa.PENDENTE, nullable=False)
    prioridade = Column(Enum(PrioridadeTarefa), default=PrioridadeTarefa.MEDIA, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    data_inicio = Column(DateTime, nullable=True)
    data_prazo = Column(DateTime, nullable=True)
    data_conclusao = Column(DateTime, nullable=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    instituicao_id = Column(Integer, ForeignKey('instituicoes.id'), nullable=True)
    projeto_id = Column(Integer, ForeignKey('projetos.id'), nullable=True)
    responsavel_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    concluida = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="tarefas_criadas")
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id], back_populates="tarefas_responsavel")
    instituicao = relationship("Instituicao", back_populates="tarefas")
    projeto = relationship("Projeto", back_populates="tarefas")
    arquivos = relationship("ArquivoTarefa", back_populates="tarefa")
    comentarios = relationship("ComentarioTarefa", back_populates="tarefa")
    subtarefas = relationship("Subtarefa", back_populates="tarefa")
    
    def __repr__(self):
        return f"<Tarefa(id={self.id}, titulo='{self.titulo}', classificacao={self.classificacao}, status={self.status})>"

class Subtarefa(Base):
    """Modelo para armazenar informações de subtarefas no sistema."""
    __tablename__ = 'subtarefas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(Enum(StatusTarefa), default=StatusTarefa.PENDENTE, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    data_conclusao = Column(DateTime, nullable=True)
    tarefa_id = Column(Integer, ForeignKey('tarefas.id'), nullable=False)
    concluida = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos
    tarefa = relationship("Tarefa", back_populates="subtarefas")
    
    def __repr__(self):
        return f"<Subtarefa(id={self.id}, titulo='{self.titulo}', status={self.status})>"

class ComentarioTarefa(Base):
    """Modelo para armazenar comentários de tarefas no sistema."""
    __tablename__ = 'comentarios_tarefas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conteudo = Column(Text, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    tarefa_id = Column(Integer, ForeignKey('tarefas.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamentos
    tarefa = relationship("Tarefa", back_populates="comentarios")
    usuario = relationship("Usuario", back_populates="comentarios_tarefas")
    
    def __repr__(self):
        return f"<ComentarioTarefa(id={self.id}, tarefa_id={self.tarefa_id}, usuario_id={self.usuario_id})>"

class Projeto(Base):
    """Modelo para armazenar informações de projetos no sistema."""
    __tablename__ = 'projetos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    data_inicio = Column(DateTime, nullable=True)
    data_prazo = Column(DateTime, nullable=True)
    data_conclusao = Column(DateTime, nullable=True)
    status = Column(String(50), default="ativo", nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    instituicao_id = Column(Integer, ForeignKey('instituicoes.id'), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="projetos")
    instituicao = relationship("Instituicao", back_populates="projetos")
    tarefas = relationship("Tarefa", back_populates="projeto")
    
    def __repr__(self):
        return f"<Projeto(id={self.id}, nome='{self.nome}', status='{self.status}')>"

class Instituicao(Base):
    """Modelo para armazenar informações de instituições no sistema."""
    __tablename__ = 'instituicoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    endereco = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    site = Column(String(255), nullable=True)
    data_cadastro = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    projetos = relationship("Projeto", back_populates="instituicao")
    tarefas = relationship("Tarefa", back_populates="instituicao")
    arquivos = relationship("Arquivo", back_populates="instituicao")
    usuarios = relationship("UsuarioInstituicao", back_populates="instituicao")
    
    def __repr__(self):
        return f"<Instituicao(id={self.id}, nome='{self.nome}')>"

class UsuarioInstituicao(Base):
    """Modelo para associação entre usuários e instituições."""
    __tablename__ = 'usuarios_instituicoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    instituicao_id = Column(Integer, ForeignKey('instituicoes.id'), nullable=False)
    cargo = Column(String(100), nullable=True)
    data_associacao = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="instituicoes")
    instituicao = relationship("Instituicao", back_populates="usuarios")
    
    def __repr__(self):
        return f"<UsuarioInstituicao(id={self.id}, usuario_id={self.usuario_id}, instituicao_id={self.instituicao_id})>"

class EventoCalendario(Base):
    """Modelo para armazenar eventos do calendário no sistema."""
    __tablename__ = 'eventos_calendario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    dia_todo = Column(Boolean, default=False, nullable=False)
    cor = Column(String(20), default="#0d6efd", nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tarefa_id = Column(Integer, ForeignKey('tarefas.id'), nullable=True)
    google_event_id = Column(String(255), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="eventos")
    
    def __repr__(self):
        return f"<EventoCalendario(id={self.id}, titulo='{self.titulo}', data_inicio='{self.data_inicio}')>"
