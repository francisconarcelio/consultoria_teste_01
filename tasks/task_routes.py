"""
Rotas para o sistema de classificação de tarefas do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc
from datetime import datetime, timedelta
import json

# Importar modelos e configurações
from .task_models import Tarefa, Subtarefa, ComentarioTarefa, Projeto, Instituicao, EventoCalendario
from .task_models import ClassificacaoTarefa, StatusTarefa, PrioridadeTarefa
from .task_forms import (TarefaForm, SubtarefaForm, ComentarioTarefaForm, ProjetoForm, 
                         InstituicaoForm, EventoCalendarioForm, FiltroTarefasForm)
from .task_utils import sincronizar_com_google_calendar, notificar_usuario

# Importar extensões da aplicação
from auth import db

# Configuração do Blueprint
tasks_bp = Blueprint('tasks', __name__, template_folder='templates')

# Rotas para Tarefas
@tasks_bp.route('/tarefas')
@login_required
def listar_tarefas():
    """
    Lista as tarefas do usuário atual com opções de filtro.
    """
    form = FiltroTarefasForm()
    
    # Carregar opções para os campos de seleção
    form.responsavel_id.choices = [(0, 'Todos')] + [
        (u.id, u.nome_completo) for u in Usuario.query.all()
    ]
    form.instituicao_id.choices = [(0, 'Todas')] + [
        (i.id, i.nome) for i in Instituicao.query.all()
    ]
    form.projeto_id.choices = [(0, 'Todos')] + [
        (p.id, p.nome) for p in Projeto.query.all()
    ]
    
    # Obter parâmetros de filtro
    classificacao = request.args.get('classificacao', '')
    status = request.args.get('status', '')
    prioridade = request.args.get('prioridade', '')
    responsavel_id = request.args.get('responsavel_id', '0')
    instituicao_id = request.args.get('instituicao_id', '0')
    projeto_id = request.args.get('projeto_id', '0')
    termo = request.args.get('termo', '')
    
    # Construir query base
    query = Tarefa.query.filter(
        or_(
            Tarefa.usuario_id == current_user.id,
            Tarefa.responsavel_id == current_user.id
        )
    )
    
    # Aplicar filtros
    if classificacao:
        query = query.filter(Tarefa.classificacao == classificacao)
    
    if status:
        query = query.filter(Tarefa.status == status)
    
    if prioridade:
        query = query.filter(Tarefa.prioridade == prioridade)
    
    if responsavel_id and responsavel_id != '0':
        query = query.filter(Tarefa.responsavel_id == int(responsavel_id))
    
    if instituicao_id and instituicao_id != '0':
        query = query.filter(Tarefa.instituicao_id == int(instituicao_id))
    
    if projeto_id and projeto_id != '0':
        query = query.filter(Tarefa.projeto_id == int(projeto_id))
    
    if termo:
        query = query.filter(
            or_(
                Tarefa.titulo.ilike(f'%{termo}%'),
                Tarefa.descricao.ilike(f'%{termo}%')
            )
        )
    
    # Ordenar por prioridade e data de prazo
    tarefas = query.order_by(
        desc(Tarefa.prioridade),
        Tarefa.data_prazo.nullslast()
    ).all()
    
    # Agrupar tarefas por classificação
    tarefas_por_classificacao = {
        'importancia': [],
        'rotina': [],
        'urgencia': [],
        'pausa': []
    }
    
    for tarefa in tarefas:
        classificacao = tarefa.classificacao.value
        tarefas_por_classificacao[classificacao].append(tarefa)
    
    return render_template(
        'tasks/listar_tarefas.html',
        tarefas_por_classificacao=tarefas_por_classificacao,
        form=form,
        classificacao=classificacao,
        status=status,
        prioridade=prioridade,
        responsavel_id=responsavel_id,
        instituicao_id=instituicao_id,
        projeto_id=projeto_id,
        termo=termo
    )

@tasks_bp.route('/tarefas/nova', methods=['GET', 'POST'])
@login_required
def nova_tarefa():
    """
    Página e processamento para criação de nova tarefa.
    """
    form = TarefaForm()
    
    # Carregar opções para os campos de seleção
    form.responsavel_id.choices = [(0, 'Nenhum')] + [
        (u.id, u.nome_completo) for u in Usuario.query.all()
    ]
    form.instituicao_id.choices = [(0, 'Nenhuma')] + [
        (i.id, i.nome) for i in Instituicao.query.all()
    ]
    form.projeto_id.choices = [(0, 'Nenhum')] + [
        (p.id, p.nome) for p in Projeto.query.all()
    ]
    
    if form.validate_on_submit():
        try:
            # Criar nova tarefa
            nova_tarefa = Tarefa(
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                classificacao=ClassificacaoTarefa(form.classificacao.data),
                status=StatusTarefa(form.status.data),
                prioridade=PrioridadeTarefa(form.prioridade.data),
                data_inicio=form.data_inicio.data,
                data_prazo=form.data_prazo.data,
                usuario_id=current_user.id,
                responsavel_id=form.responsavel_id.data if form.responsavel_id.data != 0 else None,
                instituicao_id=form.instituicao_id.data if form.instituicao_id.data != 0 else None,
                projeto_id=form.projeto_id.data if form.projeto_id.data != 0 else None,
                concluida=form.concluida.data
            )
            
            # Se a tarefa for marcada como concluída, definir data de conclusão
            if form.concluida.data:
                nova_tarefa.data_conclusao = datetime.now()
                nova_tarefa.status = StatusTarefa.CONCLUIDA
            
            db.session.add(nova_tarefa)
            db.session.commit()
            
            # Criar evento no calendário se houver data de início e prazo
            if form.data_inicio.data and form.data_prazo.data:
                evento = EventoCalendario(
                    titulo=f"Tarefa: {form.titulo.data}",
                    descricao=form.descricao.data,
                    data_inicio=form.data_inicio.data,
                    data_fim=form.data_prazo.data,
                    dia_todo=False,
                    cor=obter_cor_por_prioridade(form.prioridade.data),
                    usuario_id=current_user.id,
                    tarefa_id=nova_tarefa.id
                )
                
                db.session.add(evento)
                db.session.commit()
                
                # Sincronizar com Google Calendar se configurado
                if current_user.google_token:
                    sincronizar_com_google_calendar(evento)
            
            # Notificar responsável se for diferente do criador
            if nova_tarefa.responsavel_id and nova_tarefa.responsavel_id != current_user.id:
                notificar_usuario(
                    nova_tarefa.responsavel_id,
                    f"Nova tarefa atribuída: {nova_tarefa.titulo}",
                    f"Você foi designado como responsável por uma nova tarefa: {nova_tarefa.titulo}"
                )
            
            flash('Tarefa criada com sucesso!', 'success')
            return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=nova_tarefa.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tarefa: {str(e)}', 'danger')
    
    return render_template('tasks/form_tarefa.html', form=form, titulo='Nova Tarefa')

@tasks_bp.route('/tarefas/<int:tarefa_id>')
@login_required
def visualizar_tarefa(tarefa_id):
    """
    Visualiza detalhes de uma tarefa específica.
    """
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Verificar se o usuário tem acesso à tarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para acessar esta tarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    # Formulário para adicionar comentário
    form_comentario = ComentarioTarefaForm()
    form_comentario.tarefa_id.data = tarefa_id
    
    # Formulário para adicionar subtarefa
    form_subtarefa = SubtarefaForm()
    form_subtarefa.tarefa_id.data = tarefa_id
    
    return render_template(
        'tasks/visualizar_tarefa.html',
        tarefa=tarefa,
        form_comentario=form_comentario,
        form_subtarefa=form_subtarefa
    )

@tasks_bp.route('/tarefas/<int:tarefa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tarefa(tarefa_id):
    """
    Página e processamento para edição de tarefa existente.
    """
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Verificar se o usuário tem permissão para editar a tarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para editar esta tarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    form = TarefaForm(obj=tarefa)
    
    # Carregar opções para os campos de seleção
    form.responsavel_id.choices = [(0, 'Nenhum')] + [
        (u.id, u.nome_completo) for u in Usuario.query.all()
    ]
    form.instituicao_id.choices = [(0, 'Nenhuma')] + [
        (i.id, i.nome) for i in Instituicao.query.all()
    ]
    form.projeto_id.choices = [(0, 'Nenhum')] + [
        (p.id, p.nome) for p in Projeto.query.all()
    ]
    
    if form.validate_on_submit():
        try:
            # Verificar se o status mudou para concluído
            status_alterado_para_concluido = (
                tarefa.status != StatusTarefa.CONCLUIDA and 
                form.status.data == 'concluida'
            )
            
            # Verificar se a conclusão foi alterada
            conclusao_alterada = tarefa.concluida != form.concluida.data
            
            # Atualizar tarefa
            tarefa.titulo = form.titulo.data
            tarefa.descricao = form.descricao.data
            tarefa.classificacao = ClassificacaoTarefa(form.classificacao.data)
            tarefa.status = StatusTarefa(form.status.data)
            tarefa.prioridade = PrioridadeTarefa(form.prioridade.data)
            tarefa.data_inicio = form.data_inicio.data
            tarefa.data_prazo = form.data_prazo.data
            tarefa.responsavel_id = form.responsavel_id.data if form.responsavel_id.data != 0 else None
            tarefa.instituicao_id = form.instituicao_id.data if form.instituicao_id.data != 0 else None
            tarefa.projeto_id = form.projeto_id.data if form.projeto_id.data != 0 else None
            tarefa.concluida = form.concluida.data
            
            # Se a tarefa foi marcada como concluída, definir data de conclusão
            if (status_alterado_para_concluido or 
                (conclusao_alterada and form.concluida.data)):
                tarefa.data_conclusao = datetime.now()
                tarefa.status = StatusTarefa.CONCLUIDA
            
            # Se a tarefa foi desmarcada como concluída, limpar data de conclusão
            if conclusao_alterada and not form.concluida.data:
                tarefa.data_conclusao = None
            
            db.session.commit()
            
            # Atualizar evento no calendário se existir
            evento = EventoCalendario.query.filter_by(tarefa_id=tarefa.id).first()
            
            if evento and form.data_inicio.data and form.data_prazo.data:
                evento.titulo = f"Tarefa: {form.titulo.data}"
                evento.descricao = form.descricao.data
                evento.data_inicio = form.data_inicio.data
                evento.data_fim = form.data_prazo.data
                evento.cor = obter_cor_por_prioridade(form.prioridade.data)
                
                db.session.commit()
                
                # Sincronizar com Google Calendar se configurado
                if current_user.google_token and evento.google_event_id:
                    sincronizar_com_google_calendar(evento, atualizar=True)
            
            # Notificar responsável se foi alterado
            responsavel_anterior = tarefa.responsavel_id
            if (form.responsavel_id.data != 0 and 
                form.responsavel_id.data != responsavel_anterior and 
                form.responsavel_id.data != current_user.id):
                notificar_usuario(
                    form.responsavel_id.data,
                    f"Tarefa atribuída: {tarefa.titulo}",
                    f"Você foi designado como responsável pela tarefa: {tarefa.titulo}"
                )
            
            flash('Tarefa atualizada com sucesso!', 'success')
            return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tarefa: {str(e)}', 'danger')
    
    return render_template('tasks/form_tarefa.html', form=form, titulo='Editar Tarefa', tarefa=tarefa)

@tasks_bp.route('/tarefas/<int:tarefa_id>/excluir', methods=['POST'])
@login_required
def excluir_tarefa(tarefa_id):
    """
    Exclui uma tarefa específica.
    """
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Verificar se o usuário tem permissão para excluir a tarefa
    if tarefa.usuario_id != current_user.id:
        flash('Você não tem permissão para excluir esta tarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    try:
        # Excluir evento do calendário associado
        evento = EventoCalendario.query.filter_by(tarefa_id=tarefa.id).first()
        if evento:
            # Remover do Google Calendar se configurado
            if current_user.google_token and evento.google_event_id:
                sincronizar_com_google_calendar(evento, excluir=True)
            
            db.session.delete(evento)
        
        # Excluir subtarefas
        for subtarefa in tarefa.subtarefas:
            db.session.delete(subtarefa)
        
        # Excluir comentários
        for comentario in tarefa.comentarios:
            db.session.delete(comentario)
        
        # Excluir associações com arquivos
        for arquivo_tarefa in tarefa.arquivos:
            db.session.delete(arquivo_tarefa)
        
        # Excluir tarefa
        db.session.delete(tarefa)
        db.session.commit()
        
        flash('Tarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.listar_tarefas'))

@tasks_bp.route('/tarefas/<int:tarefa_id>/concluir', methods=['POST'])
@login_required
def concluir_tarefa(tarefa_id):
    """
    Marca uma tarefa como concluída.
    """
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Verificar se o usuário tem permissão para editar a tarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para concluir esta tarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    try:
        tarefa.concluida = True
        tarefa.status = StatusTarefa.CONCLUIDA
        tarefa.data_conclusao = datetime.now()
        db.session.commit()
        
        flash('Tarefa concluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao concluir tarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa.id))

@tasks_bp.route('/tarefas/<int:tarefa_id>/reabrir', methods=['POST'])
@login_required
def reabrir_tarefa(tarefa_id):
    """
    Reabre uma tarefa concluída.
    """
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Verificar se o usuário tem permissão para editar a tarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para reabrir esta tarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    try:
        tarefa.concluida = False
        tarefa.status = StatusTarefa.EM_ANDAMENTO
        tarefa.data_conclusao = None
        db.session.commit()
        
        flash('Tarefa reaberta com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao reabrir tarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa.id))

# Rotas para Subtarefas
@tasks_bp.route('/subtarefas/nova', methods=['POST'])
@login_required
def nova_subtarefa():
    """
    Processa a criação de uma nova subtarefa.
    """
    form = SubtarefaForm()
    
    if form.validate_on_submit():
        tarefa_id = form.tarefa_id.data
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        
        # Verificar se o usuário tem permissão para adicionar subtarefa
        if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
            flash('Você não tem permissão para adicionar subtarefas a esta tarefa.', 'danger')
            return redirect(url_for('tasks.listar_tarefas'))
        
        try:
            # Criar nova subtarefa
            nova_subtarefa = Subtarefa(
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                status=StatusTarefa(form.status.data),
                tarefa_id=tarefa_id,
                concluida=form.concluida.data
            )
            
            # Se a subtarefa for marcada como concluída, definir data de conclusão
            if form.concluida.data:
                nova_subtarefa.data_conclusao = datetime.now()
            
            db.session.add(nova_subtarefa)
            db.session.commit()
            
            flash('Subtarefa adicionada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar subtarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=form.tarefa_id.data))

@tasks_bp.route('/subtarefas/<int:subtarefa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_subtarefa(subtarefa_id):
    """
    Página e processamento para edição de subtarefa existente.
    """
    subtarefa = Subtarefa.query.get_or_404(subtarefa_id)
    tarefa = Tarefa.query.get_or_404(subtarefa.tarefa_id)
    
    # Verificar se o usuário tem permissão para editar a subtarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para editar esta subtarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    form = SubtarefaForm(obj=subtarefa)
    
    if form.validate_on_submit():
        try:
            # Verificar se a conclusão foi alterada
            conclusao_alterada = subtarefa.concluida != form.concluida.data
            
            # Atualizar subtarefa
            subtarefa.titulo = form.titulo.data
            subtarefa.descricao = form.descricao.data
            subtarefa.status = StatusTarefa(form.status.data)
            subtarefa.concluida = form.concluida.data
            
            # Se a subtarefa foi marcada como concluída, definir data de conclusão
            if conclusao_alterada and form.concluida.data:
                subtarefa.data_conclusao = datetime.now()
            
            # Se a subtarefa foi desmarcada como concluída, limpar data de conclusão
            if conclusao_alterada and not form.concluida.data:
                subtarefa.data_conclusao = None
            
            db.session.commit()
            
            flash('Subtarefa atualizada com sucesso!', 'success')
            return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=subtarefa.tarefa_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar subtarefa: {str(e)}', 'danger')
    
    return render_template(
        'tasks/form_subtarefa.html',
        form=form,
        titulo='Editar Subtarefa',
        subtarefa=subtarefa,
        tarefa=tarefa
    )

@tasks_bp.route('/subtarefas/<int:subtarefa_id>/excluir', methods=['POST'])
@login_required
def excluir_subtarefa(subtarefa_id):
    """
    Exclui uma subtarefa específica.
    """
    subtarefa = Subtarefa.query.get_or_404(subtarefa_id)
    tarefa = Tarefa.query.get_or_404(subtarefa.tarefa_id)
    
    # Verificar se o usuário tem permissão para excluir a subtarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para excluir esta subtarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    try:
        db.session.delete(subtarefa)
        db.session.commit()
        
        flash('Subtarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir subtarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa.id))

@tasks_bp.route('/subtarefas/<int:subtarefa_id>/concluir', methods=['POST'])
@login_required
def concluir_subtarefa(subtarefa_id):
    """
    Marca uma subtarefa como concluída.
    """
    subtarefa = Subtarefa.query.get_or_404(subtarefa_id)
    tarefa = Tarefa.query.get_or_404(subtarefa.tarefa_id)
    
    # Verificar se o usuário tem permissão para editar a subtarefa
    if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
        flash('Você não tem permissão para concluir esta subtarefa.', 'danger')
        return redirect(url_for('tasks.listar_tarefas'))
    
    try:
        subtarefa.concluida = True
        subtarefa.status = StatusTarefa.CONCLUIDA
        subtarefa.data_conclusao = datetime.now()
        db.session.commit()
        
        flash('Subtarefa concluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao concluir subtarefa: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa.id))

# Rotas para Comentários
@tasks_bp.route('/comentarios/novo', methods=['POST'])
@login_required
def novo_comentario():
    """
    Processa a criação de um novo comentário em uma tarefa.
    """
    form = ComentarioTarefaForm()
    
    if form.validate_on_submit():
        tarefa_id = form.tarefa_id.data
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        
        # Verificar se o usuário tem permissão para adicionar comentário
        if tarefa.usuario_id != current_user.id and tarefa.responsavel_id != current_user.id:
            flash('Você não tem permissão para adicionar comentários a esta tarefa.', 'danger')
            return redirect(url_for('tasks.listar_tarefas'))
        
        try:
            # Criar novo comentário
            novo_comentario = ComentarioTarefa(
                conteudo=form.conteudo.data,
                tarefa_id=tarefa_id,
                usuario_id=current_user.id
            )
            
            db.session.add(novo_comentario)
            db.session.commit()
            
            # Notificar outros envolvidos na tarefa
            if tarefa.usuario_id != current_user.id:
                notificar_usuario(
                    tarefa.usuario_id,
                    f"Novo comentário na tarefa: {tarefa.titulo}",
                    f"{current_user.nome_completo} comentou na tarefa: {tarefa.titulo}"
                )
            
            if tarefa.responsavel_id and tarefa.responsavel_id != current_user.id:
                notificar_usuario(
                    tarefa.responsavel_id,
                    f"Novo comentário na tarefa: {tarefa.titulo}",
                    f"{current_user.nome_completo} comentou na tarefa: {tarefa.titulo}"
                )
            
            flash('Comentário adicionado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar comentário: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=form.tarefa_id.data))

@tasks_bp.route('/comentarios/<int:comentario_id>/excluir', methods=['POST'])
@login_required
def excluir_comentario(comentario_id):
    """
    Exclui um comentário específico.
    """
    comentario = ComentarioTarefa.query.get_or_404(comentario_id)
    
    # Verificar se o usuário tem permissão para excluir o comentário
    if comentario.usuario_id != current_user.id:
        flash('Você não tem permissão para excluir este comentário.', 'danger')
        return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=comentario.tarefa_id))
    
    try:
        tarefa_id = comentario.tarefa_id
        db.session.delete(comentario)
        db.session.commit()
        
        flash('Comentário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir comentário: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.visualizar_tarefa', tarefa_id=tarefa_id))

# Funções auxiliares
def obter_cor_por_prioridade(prioridade):
    """
    Retorna uma cor com base na prioridade da tarefa.
    
    Args:
        prioridade: String representando a prioridade da tarefa
        
    Returns:
        String contendo código de cor hexadecimal
    """
    cores = {
        'baixa': '#28a745',    # Verde
        'media': '#ffc107',    # Amarelo
        'alta': '#fd7e14',     # Laranja
        'critica': '#dc3545'   # Vermelho
    }
    
    return cores.get(prioridade, '#0d6efd')  # Azul como padrão
