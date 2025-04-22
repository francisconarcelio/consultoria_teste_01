"""
Modelos para o sistema de gerenciamento de arquivos do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import datetime
import os
import hashlib
import magic
import uuid
from werkzeug.utils import secure_filename

Base = declarative_base()

class Arquivo(Base):
    """Modelo para armazenar informações de arquivos no sistema."""
    __tablename__ = 'arquivos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    extensao = Column(String(10), nullable=False)
    tamanho = Column(Integer, nullable=False)
    caminho = Column(String(255), nullable=False)
    hash_conteudo = Column(String(64), nullable=True)
    conteudo_texto = Column(Text, nullable=True)
    metadados = Column(Text, nullable=True)  # JSON serializado
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    instituicao_id = Column(Integer, ForeignKey('instituicoes.id'), nullable=True)
    publico = Column(Boolean, default=False, nullable=False)
    data_upload = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="arquivos")
    instituicao = relationship("Instituicao", back_populates="arquivos")
    tarefas = relationship("ArquivoTarefa", back_populates="arquivo")
    
    @staticmethod
    def gerar_nome_arquivo(nome_original):
        """
        Gera um nome de arquivo único baseado no nome original.
        
        Args:
            nome_original: Nome original do arquivo
            
        Returns:
            String contendo o nome de arquivo seguro e único
        """
        nome_seguro = secure_filename(nome_original)
        nome_base, extensao = os.path.splitext(nome_seguro)
        uuid_str = str(uuid.uuid4())
        return f"{nome_base}_{uuid_str}{extensao}"
    
    @staticmethod
    def calcular_hash(caminho_arquivo):
        """
        Calcula o hash SHA-256 do conteúdo de um arquivo.
        
        Args:
            caminho_arquivo: Caminho completo para o arquivo
            
        Returns:
            String contendo o hash SHA-256 do arquivo
        """
        sha256_hash = hashlib.sha256()
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def detectar_tipo_mime(caminho_arquivo):
        """
        Detecta o tipo MIME de um arquivo.
        
        Args:
            caminho_arquivo: Caminho completo para o arquivo
            
        Returns:
            String contendo o tipo MIME do arquivo
        """
        mime = magic.Magic(mime=True)
        return mime.from_file(caminho_arquivo)
    
    @staticmethod
    def extrair_texto(caminho_arquivo, tipo_mime):
        """
        Extrai o texto de um arquivo, se possível.
        
        Args:
            caminho_arquivo: Caminho completo para o arquivo
            tipo_mime: Tipo MIME do arquivo
            
        Returns:
            String contendo o texto extraído ou None se não for possível extrair
        """
        texto = None
        
        try:
            # Texto simples
            if tipo_mime == 'text/plain':
                with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                    texto = f.read()
            
            # PDF
            elif tipo_mime == 'application/pdf':
                import PyPDF2
                with open(caminho_arquivo, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    texto = ""
                    for page in reader.pages:
                        texto += page.extract_text() + "\n"
            
            # Documentos do Word
            elif tipo_mime in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                import docx2txt
                texto = docx2txt.process(caminho_arquivo)
            
        except Exception as e:
            print(f"Erro ao extrair texto: {str(e)}")
            texto = None
        
        return texto
    
    def __repr__(self):
        return f"<Arquivo(id={self.id}, nome='{self.nome}', tipo='{self.tipo}', tamanho={self.tamanho})>"


class ArquivoConteudo(Base):
    """Modelo para armazenar o conteúdo binário dos arquivos."""
    __tablename__ = 'arquivos_conteudo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_id = Column(Integer, ForeignKey('arquivos.id', ondelete='CASCADE'), nullable=False, unique=True)
    conteudo = Column(LargeBinary, nullable=False)
    
    # Relacionamentos
    arquivo = relationship("Arquivo", backref="conteudo_ref", uselist=False)
    
    def __repr__(self):
        return f"<ArquivoConteudo(id={self.id}, arquivo_id={self.arquivo_id})>"


class ArquivoTarefa(Base):
    """Modelo para associação entre arquivos e tarefas."""
    __tablename__ = 'arquivos_tarefas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_id = Column(Integer, ForeignKey('arquivos.id'), nullable=False)
    tarefa_id = Column(Integer, ForeignKey('tarefas.id'), nullable=False)
    data_associacao = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    arquivo = relationship("Arquivo", back_populates="tarefas")
    tarefa = relationship("Tarefa", back_populates="arquivos")
    
    def __repr__(self):
        return f"<ArquivoTarefa(id={self.id}, arquivo_id={self.arquivo_id}, tarefa_id={self.tarefa_id})>"
