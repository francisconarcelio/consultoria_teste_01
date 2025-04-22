"""
Utilitários para o dashboard administrativo do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime, timedelta
from flask import current_app
import xlsxwriter
import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func, desc

# Importar modelos
from .admin_models import LogSistema, Configuracao, Estatistica, Backup
from auth.auth_models import Usuario, PerfilUsuario
from tasks.task_models import Tarefa, Subtarefa, ComentarioTarefa
from files.file_models import Arquivo

# Importar extensões da aplicação
from auth import db

def calcular_estatisticas(periodo_inicio=None, periodo_fim=None):
    """
    Calcula estatísticas do sistema para o período especificado.
    
    Args:
        periodo_inicio: Data de início do período (opcional)
        periodo_fim: Data de fim do período (opcional)
        
    Returns:
        Dict contendo estatísticas calculadas
    """
    # Definir período padrão se não especificado
    if not periodo_inicio:
        periodo_inicio = datetime.now() - timedelta(days=30)
    if not periodo_fim:
        periodo_fim = datetime.now()
    
    # Estatísticas de usuários
    total_usuarios = Usuario.query.count()
    usuarios_ativos = Usuario.query.filter_by(ativo=True).count()
    usuarios_por_perfil = db.session.query(
        PerfilUsuario.nome, func.count(Usuario.id)
    ).join(
        Usuario, Usuario.perfil_id == PerfilUsuario.id
    ).group_by(
        PerfilUsuario.nome
    ).all()
    
    # Estatísticas de tarefas
    total_tarefas = Tarefa.query.count()
    tarefas_periodo = Tarefa.query.filter(
        Tarefa.data_criacao >= periodo_inicio,
        Tarefa.data_criacao <= periodo_fim
    ).count()
    tarefas_concluidas = Tarefa.query.filter_by(concluida=True).count()
    tarefas_pendentes = Tarefa.query.filter_by(concluida=False).count()
    tarefas_por_classificacao = db.session.query(
        Tarefa.classificacao, func.count(Tarefa.id)
    ).group_by(
        Tarefa.classificacao
    ).all()
    tarefas_por_status = db.session.query(
        Tarefa.status, func.count(Tarefa.id)
    ).group_by(
        Tarefa.status
    ).all()
    
    # Estatísticas de arquivos
    total_arquivos = Arquivo.query.count()
    arquivos_periodo = Arquivo.query.filter(
        Arquivo.data_upload >= periodo_inicio,
        Arquivo.data_upload <= periodo_fim
    ).count()
    tamanho_total_arquivos = db.session.query(func.sum(Arquivo.tamanho)).scalar() or 0
    arquivos_por_tipo = db.session.query(
        Arquivo.tipo, func.count(Arquivo.id)
    ).group_by(
        Arquivo.tipo
    ).all()
    
    # Estatísticas de atividades
    logs_periodo = LogSistema.query.filter(
        LogSistema.data_criacao >= periodo_inicio,
        LogSistema.data_criacao <= periodo_fim
    ).count()
    logs_por_tipo = db.session.query(
        LogSistema.tipo, func.count(LogSistema.id)
    ).filter(
        LogSistema.data_criacao >= periodo_inicio,
        LogSistema.data_criacao <= periodo_fim
    ).group_by(
        LogSistema.tipo
    ).all()
    logs_por_nivel = db.session.query(
        LogSistema.nivel, func.count(LogSistema.id)
    ).filter(
        LogSistema.data_criacao >= periodo_inicio,
        LogSistema.data_criacao <= periodo_fim
    ).group_by(
        LogSistema.nivel
    ).all()
    
    # Compilar estatísticas
    estatisticas = {
        'periodo': {
            'inicio': periodo_inicio.isoformat(),
            'fim': periodo_fim.isoformat()
        },
        'usuarios': {
            'total': total_usuarios,
            'ativos': usuarios_ativos,
            'por_perfil': {perfil: count for perfil, count in usuarios_por_perfil}
        },
        'tarefas': {
            'total': total_tarefas,
            'periodo': tarefas_periodo,
            'concluidas': tarefas_concluidas,
            'pendentes': tarefas_pendentes,
            'por_classificacao': {str(classificacao): count for classificacao, count in tarefas_por_classificacao},
            'por_status': {str(status): count for status, count in tarefas_por_status}
        },
        'arquivos': {
            'total': total_arquivos,
            'periodo': arquivos_periodo,
            'tamanho_total': tamanho_total_arquivos,
            'por_tipo': {tipo: count for tipo, count in arquivos_por_tipo}
        },
        'atividades': {
            'logs_periodo': logs_periodo,
            'por_tipo': {tipo: count for tipo, count in logs_por_tipo},
            'por_nivel': {nivel: count for nivel, count in logs_por_nivel}
        }
    }
    
    # Salvar estatísticas no banco de dados
    try:
        # Estatísticas de usuários
        estatistica_usuarios = Estatistica(
            categoria='usuarios',
            dados=estatisticas['usuarios'],
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        db.session.add(estatistica_usuarios)
        
        # Estatísticas de tarefas
        estatistica_tarefas = Estatistica(
            categoria='tarefas',
            dados=estatisticas['tarefas'],
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        db.session.add(estatistica_tarefas)
        
        # Estatísticas de arquivos
        estatistica_arquivos = Estatistica(
            categoria='arquivos',
            dados=estatisticas['arquivos'],
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        db.session.add(estatistica_arquivos)
        
        # Estatísticas de atividades
        estatistica_atividades = Estatistica(
            categoria='atividades',
            dados=estatisticas['atividades'],
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        db.session.add(estatistica_atividades)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar estatísticas: {str(e)}")
    
    return estatisticas

def criar_backup_sistema(nome, descricao=None, tipo='completo', incluir_arquivos=True, usuario_id=None):
    """
    Cria um backup do sistema.
    
    Args:
        nome: Nome do backup
        descricao: Descrição do backup (opcional)
        tipo: Tipo de backup ('completo' ou 'parcial')
        incluir_arquivos: Se deve incluir arquivos no backup
        usuario_id: ID do usuário que está criando o backup
        
    Returns:
        Dict com informações do backup criado ou None em caso de erro
    """
    try:
        # Criar diretório de backups se não existir
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Criar nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{nome.replace(' ', '_')}_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Criar diretório temporário para arquivos de backup
        with tempfile.TemporaryDirectory() as temp_dir:
            # Exportar dados do banco de dados
            exportar_dados_db(temp_dir)
            
            # Incluir arquivos se solicitado
            if incluir_arquivos:
                exportar_arquivos(temp_dir)
            
            # Criar arquivo ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
        
        # Obter tamanho do arquivo
        tamanho = os.path.getsize(backup_path)
        
        # Registrar backup no banco de dados
        backup = Backup(
            nome=nome,
            descricao=descricao,
            caminho=backup_path,
            tamanho=tamanho,
            tipo=tipo,
            status='sucesso',
            usuario_id=usuario_id
        )
        
        db.session.add(backup)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='info',
            mensagem=f'Backup {nome} criado com sucesso',
            usuario_id=usuario_id
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            'id': backup.id,
            'nome': backup.nome,
            'caminho': backup.caminho,
            'tamanho': backup.tamanho,
            'status': backup.status
        }
        
    except Exception as e:
        db.session.rollback()
        
        # Registrar log de erro
        log = LogSistema(
            tipo='erro',
            nivel='error',
            mensagem=f'Erro ao criar backup: {str(e)}',
            usuario_id=usuario_id
        )
        db.session.add(log)
        db.session.commit()
        
        print(f"Erro ao criar backup: {str(e)}")
        return None

def exportar_dados_db(diretorio):
    """
    Exporta dados do banco de dados para arquivos JSON.
    
    Args:
        diretorio: Diretório onde os arquivos serão salvos
    """
    # Criar diretório para dados
    dados_dir = os.path.join(diretorio, 'dados')
    os.makedirs(dados_dir, exist_ok=True)
    
    # Exportar usuários
    usuarios = Usuario.query.all()
    usuarios_data = [
        {
            'id': u.id,
            'nome': u.nome,
            'sobrenome': u.sobrenome,
            'email': u.email,
            'perfil_id': u.perfil_id,
            'ativo': u.ativo,
            'data_cadastro': u.data_cadastro.isoformat() if u.data_cadastro else None
        }
        for u in usuarios
    ]
    with open(os.path.join(dados_dir, 'usuarios.json'), 'w') as f:
        json.dump(usuarios_data, f, indent=2)
    
    # Exportar perfis de usuário
    perfis = PerfilUsuario.query.all()
    perfis_data = [
        {
            'id': p.id,
            'nome': p.nome,
            'descricao': p.descricao
        }
        for p in perfis
    ]
    with open(os.path.join(dados_dir, 'perfis.json'), 'w') as f:
        json.dump(perfis_data, f, indent=2)
    
    # Exportar tarefas
    tarefas = Tarefa.query.all()
    tarefas_data = [
        {
            'id': t.id,
            'titulo': t.titulo,
            'descricao': t.descricao,
            'classificacao': t.classificacao.value if t.classificacao else None,
            'status': t.status.value if t.status else None,
            'prioridade': t.prioridade.value if t.prioridade else None,
            'data_criacao': t.data_criacao.isoformat() if t.data_criacao else None,
            'data_atualizacao': t.data_atualizacao.isoformat() if t.data_atualizacao else None,
            'data_inicio': t.data_inicio.isoformat() if t.data_inicio else None,
            'data_prazo': t.data_prazo.isoformat() if t.data_prazo else None,
            'data_conclusao': t.data_conclusao.isoformat() if t.data_conclusao else None,
            'usuario_id': t.usuario_id,
            'responsavel_id': t.responsavel_id,
            'instituicao_id': t.instituicao_id,
            'projeto_id': t.projeto_id,
            'concluida': t.concluida
        }
        for t in tarefas
    ]
    with open(os.path.join(dados_dir, 'tarefas.json'), 'w') as f:
        json.dump(tarefas_data, f, indent=2)
    
    # Exportar subtarefas
    subtarefas = Subtarefa.query.all()
    subtarefas_data = [
        {
            'id': s.id,
            'titulo': s.titulo,
            'descricao': s.descricao,
            'status': s.status.value if s.status else None,
            'data_criacao': s.data_criacao.isoformat() if s.data_criacao else None,
            'data_atualizacao': s.data_atualizacao.isoformat() if s.data_atualizacao else None,
            'data_conclusao': s.data_conclusao.isoformat() if s.data_conclusao else None,
            'tarefa_id': s.tarefa_id,
            'concluida': s.concluida
        }
        for s in subtarefas
    ]
    with open(os.path.join(dados_dir, 'subtarefas.json'), 'w') as f:
        json.dump(subtarefas_data, f, indent=2)
    
    # Exportar informações de arquivos (sem conteúdo binário)
    arquivos = Arquivo.query.all()
    arquivos_data = [
        {
            'id': a.id,
            'nome': a.nome,
            'tipo': a.tipo,
            'tamanho': a.tamanho,
            'data_upload': a.data_upload.isoformat() if a.data_upload else None,
            'usuario_id': a.usuario_id,
            'descricao': a.descricao,
            'caminho': a.caminho
        }
        for a in arquivos
    ]
    with open(os.path.join(dados_dir, 'arquivos.json'), 'w') as f:
        json.dump(arquivos_data, f, indent=2)
    
    # Exportar configurações
    configuracoes = Configuracao.query.all()
    configuracoes_data = [
        {
            'id': c.id,
            'chave': c.chave,
            'valor': c.valor,
            'descricao': c.descricao,
            'tipo': c.tipo,
            'categoria': c.categoria,
            'data_atualizacao': c.data_atualizacao.isoformat() if c.data_atualizacao else None
        }
        for c in configuracoes
    ]
    with open(os.path.join(dados_dir, 'configuracoes.json'), 'w') as f:
        json.dump(configuracoes_data, f, indent=2)

def exportar_arquivos(diretorio):
    """
    Exporta arquivos do sistema para o diretório de backup.
    
    Args:
        diretorio: Diretório onde os arquivos serão salvos
    """
    # Criar diretório para arquivos
    arquivos_dir = os.path.join(diretorio, 'arquivos')
    os.makedirs(arquivos_dir, exist_ok=True)
    
    # Obter arquivos do banco de dados
    arquivos = Arquivo.query.all()
    
    # Copiar arquivos
    for arquivo in arquivos:
        if arquivo.caminho and os.path.exists(arquivo.caminho):
            # Criar diretório para o usuário
            usuario_dir = os.path.join(arquivos_dir, f"usuario_{arquivo.usuario_id}")
            os.makedirs(usuario_dir, exist_ok=True)
            
            # Definir caminho de destino
            dest_path = os.path.join(usuario_dir, os.path.basename(arquivo.caminho))
            
            # Copiar arquivo
            shutil.copy2(arquivo.caminho, dest_path)

def restaurar_backup(backup_id, usuario_id=None):
    """
    Restaura um backup do sistema.
    
    Args:
        backup_id: ID do backup a ser restaurado
        usuario_id: ID do usuário que está restaurando o backup
        
    Returns:
        Boolean indicando sucesso ou falha
    """
    try:
        # Obter backup
        backup = Backup.query.get(backup_id)
        if not backup or not os.path.exists(backup.caminho):
            return False
        
        # Criar diretório temporário para extração
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extrair backup
            with zipfile.ZipFile(backup.caminho, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restaurar dados do banco de dados
            restaurar_dados_db(os.path.join(temp_dir, 'dados'))
            
            # Restaurar arquivos se existirem
            arquivos_dir = os.path.join(temp_dir, 'arquivos')
            if os.path.exists(arquivos_dir):
                restaurar_arquivos(arquivos_dir)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='warning',
            mensagem=f'Backup {backup.nome} restaurado com sucesso',
            usuario_id=usuario_id
        )
        db.session.add(log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        
        # Registrar log de erro
        log = LogSistema(
            tipo='erro',
            nivel='error',
            mensagem=f'Erro ao restaurar backup: {str(e)}',
            usuario_id=usuario_id
        )
        db.session.add(log)
        db.session.commit()
        
        print(f"Erro ao restaurar backup: {str(e)}")
        return False

def restaurar_dados_db(diretorio):
    """
    Restaura dados do banco de dados a partir de arquivos JSON.
    
    Args:
        diretorio: Diretório onde os arquivos estão salvos
    """
    # Limpar tabelas existentes (ordem inversa de dependência)
    db.session.query(Subtarefa).delete()
    db.session.query(ComentarioTarefa).delete()
    db.session.query(Tarefa).delete()
    db.session.query(Arquivo).delete()
    db.session.query(Usuario).delete()
    db.session.query(PerfilUsuario).delete()
    db.session.query(Configuracao).delete()
    db.session.commit()
    
    # Restaurar perfis de usuário
    perfis_path = os.path.join(diretorio, 'perfis.json')
    if os.path.exists(perfis_path):
        with open(perfis_path, 'r') as f:
            perfis_data = json.load(f)
            for perfil_data in perfis_data:
                perfil = PerfilUsuario(
                    id=perfil_data['id'],
                    nome=perfil_data['nome'],
                    descricao=perfil_data['descricao']
                )
                db.session.add(perfil)
        db.session.commit()
    
    # Restaurar usuários
    usuarios_path = os.path.join(diretorio, 'usuarios.json')
    if os.path.exists(usuarios_path):
        with open(usuarios_path, 'r') as f:
            usuarios_data = json.load(f)
            for usuario_data in usuarios_data:
                data_cadastro = None
                if usuario_data.get('data_cadastro'):
                    data_cadastro = datetime.fromisoformat(usuario_data['data_cadastro'])
                
                usuario = Usuario(
                    id=usuario_data['id'],
                    nome=usuario_data['nome'],
                    sobrenome=usuario_data['sobrenome'],
                    email=usuario_data['email'],
                    perfil_id=usuario_data['perfil_id'],
                    ativo=usuario_data['ativo'],
                    data_cadastro=data_cadastro
                )
                db.session.add(usuario)
        db.session.commit()
    
    # Restaurar configurações
    configuracoes_path = os.path.join(diretorio, 'configuracoes.json')
    if os.path.exists(configuracoes_path):
        with open(configuracoes_path, 'r') as f:
            configuracoes_data = json.load(f)
            for config_data in configuracoes_data:
                data_atualizacao = None
                if config_data.get('data_atualizacao'):
                    data_atualizacao = datetime.fromisoformat(config_data['data_atualizacao'])
                
                config = Configuracao(
                    id=config_data['id'],
                    chave=config_data['chave'],
                    valor=config_data['valor'],
                    descricao=config_data['descricao'],
                    tipo=config_data['tipo'],
                    categoria=config_data['categoria'],
                    data_atualizacao=data_atualizacao
                )
                db.session.add(config)
        db.session.commit()

def restaurar_arquivos(diretorio):
    """
    Restaura arquivos do sistema a partir do diretório de backup.
    
    Args:
        diretorio: Diretório onde os arquivos estão salvos
    """
    # Obter informações de arquivos do banco de dados
    arquivos_path = os.path.join(diretorio, '..', 'dados', 'arquivos.json')
    if not os.path.exists(arquivos_path):
        return
    
    with open(arquivos_path, 'r') as f:
        arquivos_data = json.load(f)
    
    # Criar diretório de uploads se não existir
    upload_dir = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Restaurar arquivos
    for arquivo_data in arquivos_data:
        # Verificar se o arquivo existe no backup
        usuario_dir = os.path.join(diretorio, f"usuario_{arquivo_data['usuario_id']}")
        if not os.path.exists(usuario_dir):
            continue
        
        # Obter nome do arquivo original
        nome_arquivo = os.path.basename(arquivo_data['caminho'])
        arquivo_backup = os.path.join(usuario_dir, nome_arquivo)
        
        if not os.path.exists(arquivo_backup):
            continue
        
        # Criar diretório para o usuário no destino
        dest_dir = os.path.join(upload_dir, f"usuario_{arquivo_data['usuario_id']}")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Definir caminho de destino
        dest_path = os.path.join(dest_dir, nome_arquivo)
        
        # Copiar arquivo
        shutil.copy2(arquivo_backup, dest_path)
        
        # Atualizar caminho no banco de dados
        arquivo = Arquivo(
            id=arquivo_data['id'],
            nome=arquivo_data['nome'],
            tipo=arquivo_data['tipo'],
            tamanho=arquivo_data['tamanho'],
            data_upload=datetime.fromisoformat(arquivo_data['data_upload']) if arquivo_data.get('data_upload') else None,
            usuario_id=arquivo_data['usuario_id'],
            descricao=arquivo_data['descricao'],
            caminho=dest_path
        )
        db.session.add(arquivo)
    
    db.session.commit()

def gerar_relatorio_pdf(tipo, periodo_inicio=None, periodo_fim=None, nome=None):
    """
    Gera um relatório em formato PDF.
    
    Args:
        tipo: Tipo de relatório ('usuarios', 'tarefas', 'arquivos', 'atividades')
        periodo_inicio: Data de início do período (opcional)
        periodo_fim: Data de fim do período (opcional)
        nome: Nome do relatório (opcional)
        
    Returns:
        Caminho do arquivo PDF gerado ou None em caso de erro
    """
    try:
        # Definir período padrão se não especificado
        if not periodo_inicio:
            periodo_inicio = datetime.now() - timedelta(days=30)
        if not periodo_fim:
            periodo_fim = datetime.now()
        
        # Definir nome padrão se não especificado
        if not nome:
            nome = f"Relatório de {tipo.capitalize()}"
        
        # Criar diretório de relatórios se não existir
        relatorios_dir = os.path.join(current_app.instance_path, 'relatorios')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Criar nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"{nome.replace(' ', '_')}_{timestamp}.pdf"
        pdf_path = os.path.join(relatorios_dir, pdf_filename)
        
        # Obter dados para o relatório
        dados = obter_dados_relatorio(tipo, periodo_inicio, periodo_fim)
        
        # Criar documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        titulo_estilo = estilos['Heading1']
        subtitulo_estilo = estilos['Heading2']
        normal_estilo = estilos['Normal']
        
        # Título
        elementos.append(Paragraph(nome, titulo_estilo))
        elementos.append(Spacer(1, 12))
        
        # Período
        periodo_texto = f"Período: {periodo_inicio.strftime('%d/%m/%Y')} a {periodo_fim.strftime('%d/%m/%Y')}"
        elementos.append(Paragraph(periodo_texto, normal_estilo))
        elementos.append(Spacer(1, 12))
        
        # Conteúdo específico por tipo
        if tipo == 'usuarios':
            elementos.extend(gerar_conteudo_relatorio_usuarios(dados, subtitulo_estilo, normal_estilo))
        elif tipo == 'tarefas':
            elementos.extend(gerar_conteudo_relatorio_tarefas(dados, subtitulo_estilo, normal_estilo))
        elif tipo == 'arquivos':
            elementos.extend(gerar_conteudo_relatorio_arquivos(dados, subtitulo_estilo, normal_estilo))
        elif tipo == 'atividades':
            elementos.extend(gerar_conteudo_relatorio_atividades(dados, subtitulo_estilo, normal_estilo))
        
        # Construir PDF
        doc.build(elementos)
        
        return pdf_path
        
    except Exception as e:
        print(f"Erro ao gerar relatório PDF: {str(e)}")
        return None

def gerar_relatorio_excel(tipo, periodo_inicio=None, periodo_fim=None, nome=None):
    """
    Gera um relatório em formato Excel.
    
    Args:
        tipo: Tipo de relatório ('usuarios', 'tarefas', 'arquivos', 'atividades')
        periodo_inicio: Data de início do período (opcional)
        periodo_fim: Data de fim do período (opcional)
        nome: Nome do relatório (opcional)
        
    Returns:
        Caminho do arquivo Excel gerado ou None em caso de erro
    """
    try:
        # Definir período padrão se não especificado
        if not periodo_inicio:
            periodo_inicio = datetime.now() - timedelta(days=30)
        if not periodo_fim:
            periodo_fim = datetime.now()
        
        # Definir nome padrão se não especificado
        if not nome:
            nome = f"Relatório de {tipo.capitalize()}"
        
        # Criar diretório de relatórios se não existir
        relatorios_dir = os.path.join(current_app.instance_path, 'relatorios')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Criar nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"{nome.replace(' ', '_')}_{timestamp}.xlsx"
        excel_path = os.path.join(relatorios_dir, excel_filename)
        
        # Obter dados para o relatório
        dados = obter_dados_relatorio(tipo, periodo_inicio, periodo_fim)
        
        # Criar arquivo Excel
        workbook = xlsxwriter.Workbook(excel_path)
        
        # Formatos
        titulo_formato = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        cabecalho_formato = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'border': 1
        })
        celula_formato = workbook.add_format({
            'border': 1
        })
        
        # Conteúdo específico por tipo
        if tipo == 'usuarios':
            gerar_excel_relatorio_usuarios(workbook, dados, titulo_formato, cabecalho_formato, celula_formato)
        elif tipo == 'tarefas':
            gerar_excel_relatorio_tarefas(workbook, dados, titulo_formato, cabecalho_formato, celula_formato)
        elif tipo == 'arquivos':
            gerar_excel_relatorio_arquivos(workbook, dados, titulo_formato, cabecalho_formato, celula_formato)
        elif tipo == 'atividades':
            gerar_excel_relatorio_atividades(workbook, dados, titulo_formato, cabecalho_formato, celula_formato)
        
        # Fechar arquivo
        workbook.close()
        
        return excel_path
        
    except Exception as e:
        print(f"Erro ao gerar relatório Excel: {str(e)}")
        return None

def gerar_relatorio_csv(tipo, periodo_inicio=None, periodo_fim=None, nome=None):
    """
    Gera um relatório em formato CSV.
    
    Args:
        tipo: Tipo de relatório ('usuarios', 'tarefas', 'arquivos', 'atividades')
        periodo_inicio: Data de início do período (opcional)
        periodo_fim: Data de fim do período (opcional)
        nome: Nome do relatório (opcional)
        
    Returns:
        Caminho do arquivo CSV gerado ou None em caso de erro
    """
    try:
        # Definir período padrão se não especificado
        if not periodo_inicio:
            periodo_inicio = datetime.now() - timedelta(days=30)
        if not periodo_fim:
            periodo_fim = datetime.now()
        
        # Definir nome padrão se não especificado
        if not nome:
            nome = f"Relatório de {tipo.capitalize()}"
        
        # Criar diretório de relatórios se não existir
        relatorios_dir = os.path.join(current_app.instance_path, 'relatorios')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Criar nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"{nome.replace(' ', '_')}_{timestamp}.csv"
        csv_path = os.path.join(relatorios_dir, csv_filename)
        
        # Obter dados para o relatório
        dados = obter_dados_relatorio(tipo, periodo_inicio, periodo_fim)
        
        # Conteúdo específico por tipo
        if tipo == 'usuarios':
            gerar_csv_relatorio_usuarios(csv_path, dados)
        elif tipo == 'tarefas':
            gerar_csv_relatorio_tarefas(csv_path, dados)
        elif tipo == 'arquivos':
            gerar_csv_relatorio_arquivos(csv_path, dados)
        elif tipo == 'atividades':
            gerar_csv_relatorio_atividades(csv_path, dados)
        
        return csv_path
        
    except Exception as e:
        print(f"Erro ao gerar relatório CSV: {str(e)}")
        return None

def obter_dados_relatorio(tipo, periodo_inicio, periodo_fim):
    """
    Obtém dados para o relatório.
    
    Args:
        tipo: Tipo de relatório ('usuarios', 'tarefas', 'arquivos', 'atividades')
        periodo_inicio: Data de início do período
        periodo_fim: Data de fim do período
        
    Returns:
        Dict contendo dados para o relatório
    """
    if tipo == 'usuarios':
        # Usuários cadastrados no período
        usuarios = Usuario.query.filter(
            Usuario.data_cadastro >= periodo_inicio,
            Usuario.data_cadastro <= periodo_fim
        ).all()
        
        # Usuários por perfil
        usuarios_por_perfil = db.session.query(
            PerfilUsuario.nome, func.count(Usuario.id)
        ).join(
            Usuario, Usuario.perfil_id == PerfilUsuario.id
        ).filter(
            Usuario.data_cadastro >= periodo_inicio,
            Usuario.data_cadastro <= periodo_fim
        ).group_by(
            PerfilUsuario.nome
        ).all()
        
        return {
            'usuarios': usuarios,
            'usuarios_por_perfil': usuarios_por_perfil,
            'total_usuarios': len(usuarios)
        }
        
    elif tipo == 'tarefas':
        # Tarefas criadas no período
        tarefas = Tarefa.query.filter(
            Tarefa.data_criacao >= periodo_inicio,
            Tarefa.data_criacao <= periodo_fim
        ).all()
        
        # Tarefas por classificação
        tarefas_por_classificacao = db.session.query(
            Tarefa.classificacao, func.count(Tarefa.id)
        ).filter(
            Tarefa.data_criacao >= periodo_inicio,
            Tarefa.data_criacao <= periodo_fim
        ).group_by(
            Tarefa.classificacao
        ).all()
        
        # Tarefas por status
        tarefas_por_status = db.session.query(
            Tarefa.status, func.count(Tarefa.id)
        ).filter(
            Tarefa.data_criacao >= periodo_inicio,
            Tarefa.data_criacao <= periodo_fim
        ).group_by(
            Tarefa.status
        ).all()
        
        # Tarefas concluídas no período
        tarefas_concluidas = Tarefa.query.filter(
            Tarefa.data_conclusao >= periodo_inicio,
            Tarefa.data_conclusao <= periodo_fim
        ).all()
        
        return {
            'tarefas': tarefas,
            'tarefas_por_classificacao': tarefas_por_classificacao,
            'tarefas_por_status': tarefas_por_status,
            'tarefas_concluidas': tarefas_concluidas,
            'total_tarefas': len(tarefas),
            'total_concluidas': len(tarefas_concluidas)
        }
        
    elif tipo == 'arquivos':
        # Arquivos enviados no período
        arquivos = Arquivo.query.filter(
            Arquivo.data_upload >= periodo_inicio,
            Arquivo.data_upload <= periodo_fim
        ).all()
        
        # Arquivos por tipo
        arquivos_por_tipo = db.session.query(
            Arquivo.tipo, func.count(Arquivo.id)
        ).filter(
            Arquivo.data_upload >= periodo_inicio,
            Arquivo.data_upload <= periodo_fim
        ).group_by(
            Arquivo.tipo
        ).all()
        
        # Tamanho total
        tamanho_total = db.session.query(func.sum(Arquivo.tamanho)).filter(
            Arquivo.data_upload >= periodo_inicio,
            Arquivo.data_upload <= periodo_fim
        ).scalar() or 0
        
        return {
            'arquivos': arquivos,
            'arquivos_por_tipo': arquivos_por_tipo,
            'tamanho_total': tamanho_total,
            'total_arquivos': len(arquivos)
        }
        
    elif tipo == 'atividades':
        # Logs no período
        logs = LogSistema.query.filter(
            LogSistema.data_criacao >= periodo_inicio,
            LogSistema.data_criacao <= periodo_fim
        ).all()
        
        # Logs por tipo
        logs_por_tipo = db.session.query(
            LogSistema.tipo, func.count(LogSistema.id)
        ).filter(
            LogSistema.data_criacao >= periodo_inicio,
            LogSistema.data_criacao <= periodo_fim
        ).group_by(
            LogSistema.tipo
        ).all()
        
        # Logs por nível
        logs_por_nivel = db.session.query(
            LogSistema.nivel, func.count(LogSistema.id)
        ).filter(
            LogSistema.data_criacao >= periodo_inicio,
            LogSistema.data_criacao <= periodo_fim
        ).group_by(
            LogSistema.nivel
        ).all()
        
        return {
            'logs': logs,
            'logs_por_tipo': logs_por_tipo,
            'logs_por_nivel': logs_por_nivel,
            'total_logs': len(logs)
        }
    
    return {}
