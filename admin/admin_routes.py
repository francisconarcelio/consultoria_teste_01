"""
Rotas para o dashboard administrativo do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func
from datetime import datetime, timedelta
import json
import os
import csv
import io
import xlsxwriter
from werkzeug.utils import secure_filename

# Importar modelos e configurações
from .admin_models import LogSistema, Configuracao, Estatistica, Notificacao, Backup, RelatorioAgendado
from .admin_forms import (ConfiguracaoForm, FiltroLogsForm, BackupForm, RestaurarBackupForm, 
                         RelatorioForm, GerenciarUsuarioForm, NotificacaoSistemaForm)
from .admin_utils import (gerar_relatorio_pdf, gerar_relatorio_excel, gerar_relatorio_csv, 
                         criar_backup_sistema, restaurar_backup, calcular_estatisticas)

# Importar modelos de outros módulos
from auth.auth_models import Usuario, PerfilUsuario
from tasks.task_models import Tarefa, Subtarefa, ComentarioTarefa
from files.file_models import Arquivo

# Importar extensões da aplicação
from auth import db

# Configuração do Blueprint
admin_bp = Blueprint('admin', __name__, template_folder='templates')

# Decorador para verificar se o usuário é administrador
def admin_required(f):
    """
    Decorador para verificar se o usuário tem perfil de administrador.
    """
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Rota para o dashboard administrativo
@admin_bp.route('/')
@admin_required
def dashboard():
    """
    Página principal do dashboard administrativo.
    """
    # Obter estatísticas gerais
    total_usuarios = Usuario.query.count()
    total_tarefas = Tarefa.query.count()
    total_arquivos = Arquivo.query.count()
    
    # Usuários por perfil
    usuarios_por_perfil = db.session.query(
        PerfilUsuario.nome, func.count(Usuario.id)
    ).join(
        Usuario, Usuario.perfil_id == PerfilUsuario.id
    ).group_by(
        PerfilUsuario.nome
    ).all()
    
    # Tarefas por classificação
    tarefas_por_classificacao = db.session.query(
        Tarefa.classificacao, func.count(Tarefa.id)
    ).group_by(
        Tarefa.classificacao
    ).all()
    
    # Tarefas por status
    tarefas_por_status = db.session.query(
        Tarefa.status, func.count(Tarefa.id)
    ).group_by(
        Tarefa.status
    ).all()
    
    # Atividade recente (logs)
    logs_recentes = LogSistema.query.order_by(
        desc(LogSistema.data_criacao)
    ).limit(10).all()
    
    # Notificações não lidas
    notificacoes_nao_lidas = Notificacao.query.filter_by(
        usuario_id=current_user.id, 
        lida=False
    ).count()
    
    return render_template(
        'admin/dashboard.html',
        total_usuarios=total_usuarios,
        total_tarefas=total_tarefas,
        total_arquivos=total_arquivos,
        usuarios_por_perfil=usuarios_por_perfil,
        tarefas_por_classificacao=tarefas_por_classificacao,
        tarefas_por_status=tarefas_por_status,
        logs_recentes=logs_recentes,
        notificacoes_nao_lidas=notificacoes_nao_lidas
    )

# Rotas para gerenciamento de usuários
@admin_bp.route('/usuarios')
@admin_required
def listar_usuarios():
    """
    Lista todos os usuários do sistema.
    """
    usuarios = Usuario.query.all()
    return render_template('admin/listar_usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@admin_required
def novo_usuario():
    """
    Página e processamento para criação de novo usuário.
    """
    form = GerenciarUsuarioForm()
    
    # Carregar opções para os campos de seleção
    form.perfil.choices = [
        (p.id, p.nome) for p in PerfilUsuario.query.all()
    ]
    
    if form.validate_on_submit():
        try:
            # Verificar se o email já existe
            if Usuario.query.filter_by(email=form.email.data).first():
                flash('Email já cadastrado.', 'danger')
                return render_template('admin/form_usuario.html', form=form, titulo='Novo Usuário')
            
            # Criar novo usuário
            novo_usuario = Usuario(
                nome=form.nome.data,
                sobrenome=form.sobrenome.data,
                email=form.email.data,
                perfil_id=form.perfil.data,
                ativo=form.ativo.data
            )
            
            # Gerar senha aleatória
            senha_temporaria = Usuario.gerar_senha_aleatoria()
            novo_usuario.set_password(senha_temporaria)
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            # Enviar email com senha temporária ou link para redefinição
            if form.redefinir_senha.data:
                token = novo_usuario.gerar_token_redefinicao_senha()
                # Enviar email com link para redefinição
                # ...
                flash(f'Usuário criado com sucesso! Um email foi enviado para {form.email.data} com instruções para definir a senha.', 'success')
            else:
                # Enviar email com senha temporária
                # ...
                flash(f'Usuário criado com sucesso! Senha temporária: {senha_temporaria}', 'success')
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Usuário {novo_usuario.email} criado por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for('admin.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')
    
    return render_template('admin/form_usuario.html', form=form, titulo='Novo Usuário')

@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_usuario(usuario_id):
    """
    Página e processamento para edição de usuário existente.
    """
    usuario = Usuario.query.get_or_404(usuario_id)
    form = GerenciarUsuarioForm(obj=usuario)
    
    # Carregar opções para os campos de seleção
    form.perfil.choices = [
        (p.id, p.nome) for p in PerfilUsuario.query.all()
    ]
    
    if form.validate_on_submit():
        try:
            # Verificar se o email já existe e não é do usuário atual
            usuario_existente = Usuario.query.filter_by(email=form.email.data).first()
            if usuario_existente and usuario_existente.id != usuario_id:
                flash('Email já cadastrado por outro usuário.', 'danger')
                return render_template('admin/form_usuario.html', form=form, titulo='Editar Usuário', usuario=usuario)
            
            # Atualizar usuário
            usuario.nome = form.nome.data
            usuario.sobrenome = form.sobrenome.data
            usuario.email = form.email.data
            usuario.perfil_id = form.perfil.data
            usuario.ativo = form.ativo.data
            
            db.session.commit()
            
            # Enviar email para redefinição de senha se solicitado
            if form.redefinir_senha.data:
                token = usuario.gerar_token_redefinicao_senha()
                # Enviar email com link para redefinição
                # ...
                flash(f'Usuário atualizado com sucesso! Um email foi enviado para {form.email.data} com instruções para redefinir a senha.', 'success')
            else:
                flash('Usuário atualizado com sucesso!', 'success')
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Usuário {usuario.email} atualizado por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for('admin.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    
    return render_template('admin/form_usuario.html', form=form, titulo='Editar Usuário', usuario=usuario)

@admin_bp.route('/usuarios/<int:usuario_id>/excluir', methods=['POST'])
@admin_required
def excluir_usuario(usuario_id):
    """
    Exclui um usuário específico.
    """
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Impedir exclusão do próprio usuário
    if usuario.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('admin.listar_usuarios'))
    
    try:
        email = usuario.email
        db.session.delete(usuario)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='warning',
            mensagem=f'Usuário {email} excluído por {current_user.email}',
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_usuarios'))

# Rotas para logs do sistema
@admin_bp.route('/logs')
@admin_required
def listar_logs():
    """
    Lista os logs do sistema com opções de filtro.
    """
    form = FiltroLogsForm()
    
    # Carregar opções para os campos de seleção
    form.usuario_id.choices = [(0, 'Todos')] + [
        (u.id, u.nome_completo) for u in Usuario.query.all()
    ]
    
    # Obter parâmetros de filtro
    tipo = request.args.get('tipo', '')
    nivel = request.args.get('nivel', '')
    usuario_id = request.args.get('usuario_id', '0')
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')
    termo = request.args.get('termo', '')
    
    # Converter datas
    data_inicio = None
    data_fim = None
    
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    
    # Construir query base
    query = LogSistema.query
    
    # Aplicar filtros
    if tipo:
        query = query.filter(LogSistema.tipo == tipo)
    
    if nivel:
        query = query.filter(LogSistema.nivel == nivel)
    
    if usuario_id and usuario_id != '0':
        query = query.filter(LogSistema.usuario_id == int(usuario_id))
    
    if data_inicio:
        query = query.filter(LogSistema.data_criacao >= data_inicio)
    
    if data_fim:
        query = query.filter(LogSistema.data_criacao <= data_fim)
    
    if termo:
        query = query.filter(
            or_(
                LogSistema.mensagem.ilike(f'%{termo}%'),
                LogSistema.detalhes.cast(String).ilike(f'%{termo}%')
            )
        )
    
    # Ordenar por data de criação (mais recentes primeiro)
    logs = query.order_by(desc(LogSistema.data_criacao)).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=50,
        error_out=False
    )
    
    return render_template(
        'admin/listar_logs.html',
        logs=logs,
        form=form,
        tipo=tipo,
        nivel=nivel,
        usuario_id=usuario_id,
        data_inicio=data_inicio_str,
        data_fim=data_fim_str,
        termo=termo
    )

# Rotas para configurações do sistema
@admin_bp.route('/configuracoes')
@admin_required
def listar_configuracoes():
    """
    Lista as configurações do sistema.
    """
    configuracoes = Configuracao.query.order_by(Configuracao.categoria, Configuracao.chave).all()
    return render_template('admin/listar_configuracoes.html', configuracoes=configuracoes)

@admin_bp.route('/configuracoes/nova', methods=['GET', 'POST'])
@admin_required
def nova_configuracao():
    """
    Página e processamento para criação de nova configuração.
    """
    form = ConfiguracaoForm()
    
    if form.validate_on_submit():
        try:
            # Verificar se a chave já existe
            if Configuracao.query.filter_by(chave=form.chave.data).first():
                flash('Chave já cadastrada.', 'danger')
                return render_template('admin/form_configuracao.html', form=form, titulo='Nova Configuração')
            
            # Criar nova configuração
            nova_configuracao = Configuracao(
                chave=form.chave.data,
                valor=form.valor.data,
                descricao=form.descricao.data,
                tipo=form.tipo.data,
                categoria=form.categoria.data
            )
            
            db.session.add(nova_configuracao)
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Configuração {nova_configuracao.chave} criada por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Configuração criada com sucesso!', 'success')
            return redirect(url_for('admin.listar_configuracoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar configuração: {str(e)}', 'danger')
    
    return render_template('admin/form_configuracao.html', form=form, titulo='Nova Configuração')

@admin_bp.route('/configuracoes/<int:configuracao_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_configuracao(configuracao_id):
    """
    Página e processamento para edição de configuração existente.
    """
    configuracao = Configuracao.query.get_or_404(configuracao_id)
    form = ConfiguracaoForm(obj=configuracao)
    
    if form.validate_on_submit():
        try:
            # Verificar se a chave já existe e não é da configuração atual
            config_existente = Configuracao.query.filter_by(chave=form.chave.data).first()
            if config_existente and config_existente.id != configuracao_id:
                flash('Chave já cadastrada por outra configuração.', 'danger')
                return render_template('admin/form_configuracao.html', form=form, titulo='Editar Configuração', configuracao=configuracao)
            
            # Atualizar configuração
            configuracao.chave = form.chave.data
            configuracao.valor = form.valor.data
            configuracao.descricao = form.descricao.data
            configuracao.tipo = form.tipo.data
            configuracao.categoria = form.categoria.data
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Configuração {configuracao.chave} atualizada por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Configuração atualizada com sucesso!', 'success')
            return redirect(url_for('admin.listar_configuracoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar configuração: {str(e)}', 'danger')
    
    return render_template('admin/form_configuracao.html', form=form, titulo='Editar Configuração', configuracao=configuracao)

@admin_bp.route('/configuracoes/<int:configuracao_id>/excluir', methods=['POST'])
@admin_required
def excluir_configuracao(configuracao_id):
    """
    Exclui uma configuração específica.
    """
    configuracao = Configuracao.query.get_or_404(configuracao_id)
    
    try:
        chave = configuracao.chave
        db.session.delete(configuracao)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='warning',
            mensagem=f'Configuração {chave} excluída por {current_user.email}',
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Configuração excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir configuração: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_configuracoes'))

# Rotas para backups do sistema
@admin_bp.route('/backups')
@admin_required
def listar_backups():
    """
    Lista os backups do sistema.
    """
    backups = Backup.query.order_by(desc(Backup.data_criacao)).all()
    return render_template('admin/listar_backups.html', backups=backups)

@admin_bp.route('/backups/novo', methods=['GET', 'POST'])
@admin_required
def novo_backup():
    """
    Página e processamento para criação de novo backup.
    """
    form = BackupForm()
    
    if form.validate_on_submit():
        try:
            # Criar backup
            backup_info = criar_backup_sistema(
                nome=form.nome.data,
                descricao=form.descricao.data,
                tipo=form.tipo.data,
                incluir_arquivos=form.incluir_arquivos.data,
                usuario_id=current_user.id
            )
            
            if backup_info:
                flash('Backup criado com sucesso!', 'success')
            else:
                flash('Erro ao criar backup.', 'danger')
            
            return redirect(url_for('admin.listar_backups'))
            
        except Exception as e:
            flash(f'Erro ao criar backup: {str(e)}', 'danger')
    
    return render_template('admin/form_backup.html', form=form, titulo='Novo Backup')

@admin_bp.route('/backups/<int:backup_id>/restaurar', methods=['GET', 'POST'])
@admin_required
def restaurar_backup_view(backup_id):
    """
    Página e processamento para restauração de backup.
    """
    backup = Backup.query.get_or_404(backup_id)
    form = RestaurarBackupForm()
    
    # Carregar opções para os campos de seleção
    form.backup_id.choices = [
        (b.id, f"{b.nome} ({b.data_criacao.strftime('%d/%m/%Y %H:%M')})")
        for b in Backup.query.filter_by(status='sucesso').order_by(desc(Backup.data_criacao)).all()
    ]
    
    if form.validate_on_submit():
        try:
            # Restaurar backup
            resultado = restaurar_backup(
                backup_id=form.backup_id.data,
                usuario_id=current_user.id
            )
            
            if resultado:
                flash('Backup restaurado com sucesso!', 'success')
            else:
                flash('Erro ao restaurar backup.', 'danger')
            
            return redirect(url_for('admin.listar_backups'))
            
        except Exception as e:
            flash(f'Erro ao restaurar backup: {str(e)}', 'danger')
    
    # Pré-selecionar o backup atual
    form.backup_id.data = backup_id
    
    return render_template('admin/form_restaurar_backup.html', form=form, backup=backup)

@admin_bp.route('/backups/<int:backup_id>/download')
@admin_required
def download_backup(backup_id):
    """
    Faz o download de um backup específico.
    """
    backup = Backup.query.get_or_404(backup_id)
    
    # Verificar se o arquivo existe
    if not os.path.exists(backup.caminho):
        flash('Arquivo de backup não encontrado.', 'danger')
        return redirect(url_for('admin.listar_backups'))
    
    # Registrar log
    log = LogSistema(
        tipo='acao',
        nivel='info',
        mensagem=f'Download do backup {backup.nome} realizado por {current_user.email}',
        usuario_id=current_user.id
    )
    db.session.add(log)
    db.session.commit()
    
    # Retornar o arquivo para download
    return send_file(
        backup.caminho,
        as_attachment=True,
        download_name=f"{backup.nome}_{backup.data_criacao.strftime('%Y%m%d_%H%M%S')}.zip"
    )

# Rotas para relatórios
@admin_bp.route('/relatorios')
@admin_required
def listar_relatorios():
    """
    Lista os relatórios agendados do sistema.
    """
    relatorios = RelatorioAgendado.query.order_by(desc(RelatorioAgendado.id)).all()
    return render_template('admin/listar_relatorios.html', relatorios=relatorios)

@admin_bp.route('/relatorios/novo', methods=['GET', 'POST'])
@admin_required
def novo_relatorio():
    """
    Página e processamento para criação de novo relatório.
    """
    form = RelatorioForm()
    
    if form.validate_on_submit():
        try:
            # Verificar se é um relatório agendado
            if form.agendar.data:
                # Criar relatório agendado
                relatorio = RelatorioAgendado(
                    nome=form.nome.data,
                    descricao=form.descricao.data,
                    tipo=form.tipo.data,
                    parametros={
                        'periodo_inicio': form.periodo_inicio.data.isoformat() if form.periodo_inicio.data else None,
                        'periodo_fim': form.periodo_fim.data.isoformat() if form.periodo_fim.data else None
                    },
                    formato=form.formato.data,
                    frequencia=form.frequencia.data,
                    proximo_agendamento=calcular_proximo_agendamento(form.frequencia.data),
                    status='ativo',
                    destinatarios=[email.strip() for email in form.destinatarios.data.split(',') if email.strip()],
                    usuario_id=current_user.id
                )
                
                db.session.add(relatorio)
                db.session.commit()
                
                flash('Relatório agendado com sucesso!', 'success')
                return redirect(url_for('admin.listar_relatorios'))
            else:
                # Gerar relatório imediatamente
                if form.formato.data == 'pdf':
                    arquivo_relatorio = gerar_relatorio_pdf(
                        tipo=form.tipo.data,
                        periodo_inicio=form.periodo_inicio.data,
                        periodo_fim=form.periodo_fim.data,
                        nome=form.nome.data
                    )
                elif form.formato.data == 'excel':
                    arquivo_relatorio = gerar_relatorio_excel(
                        tipo=form.tipo.data,
                        periodo_inicio=form.periodo_inicio.data,
                        periodo_fim=form.periodo_fim.data,
                        nome=form.nome.data
                    )
                elif form.formato.data == 'csv':
                    arquivo_relatorio = gerar_relatorio_csv(
                        tipo=form.tipo.data,
                        periodo_inicio=form.periodo_inicio.data,
                        periodo_fim=form.periodo_fim.data,
                        nome=form.nome.data
                    )
                
                if arquivo_relatorio:
                    # Registrar log
                    log = LogSistema(
                        tipo='acao',
                        nivel='info',
                        mensagem=f'Relatório {form.nome.data} gerado por {current_user.email}',
                        usuario_id=current_user.id
                    )
                    db.session.add(log)
                    db.session.commit()
                    
                    # Retornar o arquivo para download
                    return send_file(
                        arquivo_relatorio,
                        as_attachment=True,
                        download_name=f"{form.nome.data}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{form.formato.data}"
                    )
                else:
                    flash('Erro ao gerar relatório.', 'danger')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar relatório: {str(e)}', 'danger')
    
    return render_template('admin/form_relatorio.html', form=form, titulo='Novo Relatório')

@admin_bp.route('/relatorios/<int:relatorio_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_relatorio(relatorio_id):
    """
    Página e processamento para edição de relatório agendado existente.
    """
    relatorio = RelatorioAgendado.query.get_or_404(relatorio_id)
    form = RelatorioForm(obj=relatorio)
    
    # Preencher campos do formulário com dados do relatório
    if request.method == 'GET':
        form.agendar.data = True
        if relatorio.parametros:
            if 'periodo_inicio' in relatorio.parametros and relatorio.parametros['periodo_inicio']:
                form.periodo_inicio.data = datetime.fromisoformat(relatorio.parametros['periodo_inicio'])
            if 'periodo_fim' in relatorio.parametros and relatorio.parametros['periodo_fim']:
                form.periodo_fim.data = datetime.fromisoformat(relatorio.parametros['periodo_fim'])
        if relatorio.destinatarios:
            form.destinatarios.data = ','.join(relatorio.destinatarios)
    
    if form.validate_on_submit():
        try:
            # Atualizar relatório agendado
            relatorio.nome = form.nome.data
            relatorio.descricao = form.descricao.data
            relatorio.tipo = form.tipo.data
            relatorio.parametros = {
                'periodo_inicio': form.periodo_inicio.data.isoformat() if form.periodo_inicio.data else None,
                'periodo_fim': form.periodo_fim.data.isoformat() if form.periodo_fim.data else None
            }
            relatorio.formato = form.formato.data
            relatorio.frequencia = form.frequencia.data
            relatorio.proximo_agendamento = calcular_proximo_agendamento(form.frequencia.data)
            relatorio.destinatarios = [email.strip() for email in form.destinatarios.data.split(',') if email.strip()]
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Relatório agendado {relatorio.nome} atualizado por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Relatório agendado atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_relatorios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar relatório agendado: {str(e)}', 'danger')
    
    return render_template('admin/form_relatorio.html', form=form, titulo='Editar Relatório', relatorio=relatorio)

@admin_bp.route('/relatorios/<int:relatorio_id>/excluir', methods=['POST'])
@admin_required
def excluir_relatorio(relatorio_id):
    """
    Exclui um relatório agendado específico.
    """
    relatorio = RelatorioAgendado.query.get_or_404(relatorio_id)
    
    try:
        nome = relatorio.nome
        db.session.delete(relatorio)
        
        # Registrar log
        log = LogSistema(
            tipo='acao',
            nivel='warning',
            mensagem=f'Relatório agendado {nome} excluído por {current_user.email}',
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Relatório agendado excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir relatório agendado: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_relatorios'))

@admin_bp.route('/relatorios/<int:relatorio_id>/executar', methods=['POST'])
@admin_required
def executar_relatorio(relatorio_id):
    """
    Executa um relatório agendado imediatamente.
    """
    relatorio = RelatorioAgendado.query.get_or_404(relatorio_id)
    
    try:
        # Extrair parâmetros
        periodo_inicio = None
        periodo_fim = None
        
        if relatorio.parametros:
            if 'periodo_inicio' in relatorio.parametros and relatorio.parametros['periodo_inicio']:
                periodo_inicio = datetime.fromisoformat(relatorio.parametros['periodo_inicio'])
            if 'periodo_fim' in relatorio.parametros and relatorio.parametros['periodo_fim']:
                periodo_fim = datetime.fromisoformat(relatorio.parametros['periodo_fim'])
        
        # Gerar relatório
        if relatorio.formato == 'pdf':
            arquivo_relatorio = gerar_relatorio_pdf(
                tipo=relatorio.tipo,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                nome=relatorio.nome
            )
        elif relatorio.formato == 'excel':
            arquivo_relatorio = gerar_relatorio_excel(
                tipo=relatorio.tipo,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                nome=relatorio.nome
            )
        elif relatorio.formato == 'csv':
            arquivo_relatorio = gerar_relatorio_csv(
                tipo=relatorio.tipo,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                nome=relatorio.nome
            )
        
        if arquivo_relatorio:
            # Atualizar último agendamento
            relatorio.ultimo_agendamento = datetime.now()
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Relatório agendado {relatorio.nome} executado manualmente por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            # Retornar o arquivo para download
            return send_file(
                arquivo_relatorio,
                as_attachment=True,
                download_name=f"{relatorio.nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{relatorio.formato}"
            )
        else:
            flash('Erro ao gerar relatório.', 'danger')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao executar relatório: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_relatorios'))

# Rotas para notificações
@admin_bp.route('/notificacoes')
@admin_required
def listar_notificacoes():
    """
    Lista as notificações do sistema.
    """
    # Notificações recebidas pelo usuário atual
    notificacoes_recebidas = Notificacao.query.filter_by(
        usuario_id=current_user.id
    ).order_by(desc(Notificacao.data_criacao)).all()
    
    # Notificações enviadas para outros usuários (apenas para administradores)
    notificacoes_enviadas = []
    if current_user.is_admin():
        notificacoes_enviadas = db.session.query(
            Notificacao, Usuario
        ).join(
            Usuario, Notificacao.usuario_id == Usuario.id
        ).filter(
            Notificacao.usuario_id != current_user.id
        ).order_by(
            desc(Notificacao.data_criacao)
        ).limit(100).all()
    
    return render_template(
        'admin/listar_notificacoes.html',
        notificacoes_recebidas=notificacoes_recebidas,
        notificacoes_enviadas=notificacoes_enviadas
    )

@admin_bp.route('/notificacoes/nova', methods=['GET', 'POST'])
@admin_required
def nova_notificacao():
    """
    Página e processamento para criação de nova notificação.
    """
    form = NotificacaoSistemaForm()
    
    # Carregar opções para os campos de seleção
    form.usuario_id.choices = [
        (u.id, u.nome_completo) for u in Usuario.query.all()
    ]
    
    if form.validate_on_submit():
        try:
            # Determinar destinatários
            destinatarios = []
            
            if form.destinatarios.data == 'todos':
                destinatarios = [u.id for u in Usuario.query.all()]
            elif form.destinatarios.data == 'admins':
                perfil_admin = PerfilUsuario.query.filter_by(nome='admin').first()
                if perfil_admin:
                    destinatarios = [u.id for u in Usuario.query.filter_by(perfil_id=perfil_admin.id).all()]
            elif form.destinatarios.data == 'gestores':
                perfil_gestor = PerfilUsuario.query.filter_by(nome='gestor').first()
                if perfil_gestor:
                    destinatarios = [u.id for u in Usuario.query.filter_by(perfil_id=perfil_gestor.id).all()]
            elif form.destinatarios.data == 'consultores':
                perfil_consultor = PerfilUsuario.query.filter_by(nome='consultor').first()
                if perfil_consultor:
                    destinatarios = [u.id for u in Usuario.query.filter_by(perfil_id=perfil_consultor.id).all()]
            elif form.destinatarios.data == 'clientes':
                perfil_cliente = PerfilUsuario.query.filter_by(nome='cliente').first()
                if perfil_cliente:
                    destinatarios = [u.id for u in Usuario.query.filter_by(perfil_id=perfil_cliente.id).all()]
            elif form.destinatarios.data == 'especifico' and form.usuario_id.data:
                destinatarios = [form.usuario_id.data]
            
            # Criar notificações para cada destinatário
            for usuario_id in destinatarios:
                notificacao = Notificacao(
                    usuario_id=usuario_id,
                    titulo=form.titulo.data,
                    mensagem=form.mensagem.data,
                    tipo=form.tipo.data,
                    link=form.link.data
                )
                db.session.add(notificacao)
            
            # Registrar log
            log = LogSistema(
                tipo='acao',
                nivel='info',
                mensagem=f'Notificação "{form.titulo.data}" enviada para {len(destinatarios)} usuários por {current_user.email}',
                usuario_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Notificação enviada com sucesso para {len(destinatarios)} usuários!', 'success')
            return redirect(url_for('admin.listar_notificacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao enviar notificação: {str(e)}', 'danger')
    
    return render_template('admin/form_notificacao.html', form=form, titulo='Nova Notificação')

@admin_bp.route('/notificacoes/<int:notificacao_id>/marcar_lida', methods=['POST'])
@login_required
def marcar_notificacao_lida(notificacao_id):
    """
    Marca uma notificação como lida.
    """
    notificacao = Notificacao.query.get_or_404(notificacao_id)
    
    # Verificar se a notificação pertence ao usuário atual
    if notificacao.usuario_id != current_user.id:
        flash('Você não tem permissão para acessar esta notificação.', 'danger')
        return redirect(url_for('admin.listar_notificacoes'))
    
    try:
        notificacao.lida = True
        notificacao.data_leitura = datetime.now()
        db.session.commit()
        
        flash('Notificação marcada como lida.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao marcar notificação como lida: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_notificacoes'))

# Funções auxiliares
def calcular_proximo_agendamento(frequencia):
    """
    Calcula a próxima data de agendamento com base na frequência.
    
    Args:
        frequencia: String representando a frequência ('diario', 'semanal', 'mensal', 'sob_demanda')
        
    Returns:
        DateTime representando a próxima data de agendamento ou None para sob_demanda
    """
    agora = datetime.now()
    
    if frequencia == 'diario':
        # Próximo dia às 01:00
        return (agora + timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0)
    elif frequencia == 'semanal':
        # Próxima segunda-feira às 01:00
        dias_ate_segunda = 7 - agora.weekday() if agora.weekday() > 0 else 7
        return (agora + timedelta(days=dias_ate_segunda)).replace(hour=1, minute=0, second=0, microsecond=0)
    elif frequencia == 'mensal':
        # Dia 1 do próximo mês às 01:00
        if agora.month == 12:
            proximo = agora.replace(year=agora.year + 1, month=1, day=1)
        else:
            proximo = agora.replace(month=agora.month + 1, day=1)
        return proximo.replace(hour=1, minute=0, second=0, microsecond=0)
    else:
        # Sob demanda não tem próximo agendamento
        return None
