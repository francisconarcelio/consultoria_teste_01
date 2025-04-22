"""
Modelos para o dashboard administrativo do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class LogSistema(Base):
    """Modelo para armazenar logs do sistema."""
    __tablename__ = 'logs_sistema'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)  # 'acesso', 'erro', 'acao', 'seguranca'
    nivel = Column(String(20), nullable=False)  # 'info', 'warning', 'error', 'critical'
    mensagem = Column(Text, nullable=False)
    detalhes = Column(JSON, nullable=True)
    ip = Column(String(50), nullable=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="logs")
    
    def __repr__(self):
        return f"<LogSistema(id={self.id}, tipo='{self.tipo}', nivel='{self.nivel}')>"

class Configuracao(Base):
    """Modelo para armazenar configurações do sistema."""
    __tablename__ = 'configuracoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), nullable=False, unique=True)
    valor = Column(Text, nullable=True)
    descricao = Column(Text, nullable=True)
    tipo = Column(String(20), nullable=False)  # 'string', 'integer', 'boolean', 'json'
    categoria = Column(String(50), nullable=False)  # 'sistema', 'email', 'seguranca', 'integracao'
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Configuracao(chave='{self.chave}', categoria='{self.categoria}')>"

class Estatistica(Base):
    """Modelo para armazenar estatísticas do sistema."""
    __tablename__ = 'estatisticas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoria = Column(String(50), nullable=False)  # 'usuarios', 'tarefas', 'arquivos', 'acessos'
    subcategoria = Column(String(50), nullable=True)
    dados = Column(JSON, nullable=False)
    periodo_inicio = Column(DateTime, nullable=False)
    periodo_fim = Column(DateTime, nullable=False)
    data_calculo = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Estatistica(id={self.id}, categoria='{self.categoria}', periodo_inicio='{self.periodo_inicio}')>"

class Notificacao(Base):
    """Modelo para armazenar notificações do sistema."""
    __tablename__ = 'notificacoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    titulo = Column(String(255), nullable=False)
    mensagem = Column(Text, nullable=False)
    tipo = Column(String(50), nullable=False)  # 'info', 'warning', 'success', 'error'
    lida = Column(Boolean, default=False, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_leitura = Column(DateTime, nullable=True)
    link = Column(String(255), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="notificacoes")
    
    def __repr__(self):
        return f"<Notificacao(id={self.id}, usuario_id={self.usuario_id}, lida={self.lida})>"

class Backup(Base):
    """Modelo para armazenar informações de backups do sistema."""
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    caminho = Column(String(255), nullable=False)
    tamanho = Column(Integer, nullable=False)  # Em bytes
    tipo = Column(String(50), nullable=False)  # 'completo', 'parcial', 'automatico'
    status = Column(String(50), nullable=False)  # 'sucesso', 'falha', 'em_andamento'
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<Backup(id={self.id}, nome='{self.nome}', status='{self.status}')>"

class RelatorioAgendado(Base):
    """Modelo para armazenar informações de relatórios agendados."""
    __tablename__ = 'relatorios_agendados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    tipo = Column(String(50), nullable=False)  # 'usuarios', 'tarefas', 'arquivos', 'atividades'
    parametros = Column(JSON, nullable=True)
    formato = Column(String(20), nullable=False)  # 'pdf', 'excel', 'csv'
    frequencia = Column(String(50), nullable=False)  # 'diario', 'semanal', 'mensal', 'sob_demanda'
    proximo_agendamento = Column(DateTime, nullable=True)
    ultimo_agendamento = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default='ativo')  # 'ativo', 'inativo', 'pausado'
    destinatarios = Column(JSON, nullable=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<RelatorioAgendado(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')>"
