"""
Utilitários para o sistema de gerenciamento de arquivos do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

import os
import magic
import hashlib
import PyPDF2
import docx2txt
import tempfile
from PIL import Image
from werkzeug.utils import secure_filename

def validar_arquivo(caminho_arquivo, mime_type):
    """
    Valida se o arquivo é de um tipo permitido.
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        mime_type: Tipo MIME do arquivo
        
    Returns:
        Boolean indicando se o arquivo é válido
    """
    # Tipos MIME permitidos
    tipos_permitidos = [
        'application/pdf',                                                  # PDF
        'application/msword',                                               # DOC
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'text/plain'                                                        # TXT
    ]
    
    # Verificar tipo MIME
    if mime_type not in tipos_permitidos:
        return False
    
    # Verificar extensão
    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    extensoes_permitidas = ['.pdf', '.doc', '.docx', '.txt']
    if extensao not in extensoes_permitidas:
        return False
    
    # Verificar correspondência entre extensão e tipo MIME
    if extensao == '.pdf' and mime_type != 'application/pdf':
        return False
    elif extensao == '.doc' and mime_type != 'application/msword':
        return False
    elif extensao == '.docx' and mime_type != 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return False
    elif extensao == '.txt' and mime_type != 'text/plain':
        return False
    
    return True

def extrair_texto_arquivo(caminho_arquivo, mime_type):
    """
    Extrai o texto de um arquivo, se possível.
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        mime_type: Tipo MIME do arquivo
        
    Returns:
        String contendo o texto extraído ou None se não for possível extrair
    """
    texto = None
    
    try:
        # Texto simples
        if mime_type == 'text/plain':
            with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                texto = f.read()
        
        # PDF
        elif mime_type == 'application/pdf':
            texto = ""
            with open(caminho_arquivo, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texto += page_text + "\n"
        
        # Documentos do Word
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            texto = docx2txt.process(caminho_arquivo)
        
    except Exception as e:
        print(f"Erro ao extrair texto: {str(e)}")
        texto = None
    
    return texto

def gerar_thumbnail(caminho_arquivo, mime_type, tamanho=(200, 200)):
    """
    Gera uma miniatura para o arquivo, se possível.
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        mime_type: Tipo MIME do arquivo
        tamanho: Tupla (largura, altura) para a miniatura
        
    Returns:
        Caminho para a miniatura gerada ou None se não for possível gerar
    """
    thumbnail_path = None
    
    try:
        # PDF
        if mime_type == 'application/pdf':
            import fitz  # PyMuPDF
            
            # Criar nome para a miniatura
            nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
            thumbnail_path = os.path.join(tempfile.gettempdir(), f"{nome_base}_thumb.png")
            
            # Abrir PDF e renderizar primeira página
            doc = fitz.open(caminho_arquivo)
            if doc.page_count > 0:
                page = doc.load_page(0)
                pix = page.get_pixmap()
                pix.save(thumbnail_path)
                
                # Redimensionar para o tamanho desejado
                img = Image.open(thumbnail_path)
                img.thumbnail(tamanho)
                img.save(thumbnail_path)
        
        # Documentos do Word (não é possível gerar miniaturas diretamente)
        # Para documentos de texto, podemos usar ícones padrão
        
    except Exception as e:
        print(f"Erro ao gerar miniatura: {str(e)}")
        thumbnail_path = None
    
    return thumbnail_path

def calcular_hash_arquivo(caminho_arquivo):
    """
    Calcula o hash SHA-256 do conteúdo de um arquivo.
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        
    Returns:
        String contendo o hash SHA-256 do arquivo
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Erro ao calcular hash: {str(e)}")
        return None

def obter_metadados_arquivo(caminho_arquivo, mime_type):
    """
    Obtém metadados de um arquivo, se possível.
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        mime_type: Tipo MIME do arquivo
        
    Returns:
        Dicionário contendo os metadados do arquivo
    """
    metadados = {}
    
    try:
        # Metadados básicos
        metadados['tamanho'] = os.path.getsize(caminho_arquivo)
        metadados['data_modificacao'] = os.path.getmtime(caminho_arquivo)
        metadados['mime_type'] = mime_type
        
        # PDF
        if mime_type == 'application/pdf':
            with open(caminho_arquivo, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadados['paginas'] = len(reader.pages)
                
                if reader.metadata:
                    info = reader.metadata
                    if info.get('/Title'):
                        metadados['titulo'] = info.get('/Title')
                    if info.get('/Author'):
                        metadados['autor'] = info.get('/Author')
                    if info.get('/Subject'):
                        metadados['assunto'] = info.get('/Subject')
                    if info.get('/Keywords'):
                        metadados['palavras_chave'] = info.get('/Keywords')
                    if info.get('/Producer'):
                        metadados['produtor'] = info.get('/Producer')
                    if info.get('/Creator'):
                        metadados['criador'] = info.get('/Creator')
                    if info.get('/CreationDate'):
                        metadados['data_criacao'] = info.get('/CreationDate')
        
        # Documentos do Word
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            import docx
            
            doc = docx.Document(caminho_arquivo)
            metadados['paragrafos'] = len(doc.paragraphs)
            
            core_properties = doc.core_properties
            if hasattr(core_properties, 'title') and core_properties.title:
                metadados['titulo'] = core_properties.title
            if hasattr(core_properties, 'author') and core_properties.author:
                metadados['autor'] = core_properties.author
            if hasattr(core_properties, 'subject') and core_properties.subject:
                metadados['assunto'] = core_properties.subject
            if hasattr(core_properties, 'keywords') and core_properties.keywords:
                metadados['palavras_chave'] = core_properties.keywords
            if hasattr(core_properties, 'created') and core_properties.created:
                metadados['data_criacao'] = core_properties.created
            if hasattr(core_properties, 'modified') and core_properties.modified:
                metadados['data_modificacao'] = core_properties.modified
        
    except Exception as e:
        print(f"Erro ao obter metadados: {str(e)}")
    
    return metadados

def verificar_virus(caminho_arquivo):
    """
    Verifica se o arquivo contém vírus (simulação).
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo
        
    Returns:
        Boolean indicando se o arquivo está livre de vírus
    """
    # Simulação de verificação de vírus
    # Em um ambiente de produção, seria integrado com um antivírus real
    return True
