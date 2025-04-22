"""
Utilitários para o sistema de classificação de tarefas do Sistema de Consultoria Educacional
Serra Projetos Educacionais
"""

import os
import json
import requests
from datetime import datetime, timedelta
from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def sincronizar_com_google_calendar(evento, atualizar=False, excluir=False):
    """
    Sincroniza um evento com o Google Calendar.
    
    Args:
        evento: Objeto EventoCalendario a ser sincronizado
        atualizar: Boolean indicando se é uma atualização
        excluir: Boolean indicando se o evento deve ser excluído
        
    Returns:
        String contendo o ID do evento no Google Calendar ou None em caso de erro
    """
    try:
        # Obter token do usuário
        from auth.auth_models import Usuario
        usuario = Usuario.query.get(evento.usuario_id)
        
        if not usuario or not usuario.google_token:
            return None
        
        # Criar credenciais
        creds = Credentials(
            token=usuario.google_token,
            refresh_token=usuario.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        
        # Construir serviço
        service = build('calendar', 'v3', credentials=creds)
        
        # Excluir evento
        if excluir and evento.google_event_id:
            service.events().delete(
                calendarId='primary',
                eventId=evento.google_event_id
            ).execute()
            return None
        
        # Criar corpo do evento
        event_body = {
            'summary': evento.titulo,
            'description': evento.descricao or '',
            'start': {
                'dateTime': evento.data_inicio.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': evento.data_fim.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'colorId': obter_color_id_google(evento.cor),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        # Atualizar evento existente
        if atualizar and evento.google_event_id:
            updated_event = service.events().update(
                calendarId='primary',
                eventId=evento.google_event_id,
                body=event_body
            ).execute()
            return updated_event['id']
        
        # Criar novo evento
        created_event = service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
        
        return created_event['id']
        
    except HttpError as error:
        print(f'Erro ao sincronizar com Google Calendar: {error}')
        return None
    except Exception as e:
        print(f'Erro ao sincronizar com Google Calendar: {str(e)}')
        return None

def obter_color_id_google(cor_hex):
    """
    Converte uma cor hexadecimal para o ID de cor do Google Calendar.
    
    Args:
        cor_hex: String contendo código de cor hexadecimal
        
    Returns:
        String contendo o ID de cor do Google Calendar
    """
    # Mapeamento aproximado de cores hexadecimais para IDs do Google Calendar
    mapeamento_cores = {
        '#dc3545': '11',  # Vermelho
        '#fd7e14': '6',   # Laranja
        '#ffc107': '5',   # Amarelo
        '#28a745': '10',  # Verde
        '#0d6efd': '1',   # Azul
        '#6c757d': '8',   # Cinza
        '#6f42c1': '3',   # Roxo
    }
    
    return mapeamento_cores.get(cor_hex, '1')  # Azul como padrão

def notificar_usuario(usuario_id, titulo, mensagem):
    """
    Envia uma notificação para um usuário.
    
    Args:
        usuario_id: ID do usuário a ser notificado
        titulo: Título da notificação
        mensagem: Conteúdo da notificação
        
    Returns:
        Boolean indicando se a notificação foi enviada com sucesso
    """
    try:
        from auth.auth_models import Usuario, Notificacao
        from auth import db
        
        # Criar notificação
        notificacao = Notificacao(
            usuario_id=usuario_id,
            titulo=titulo,
            mensagem=mensagem,
            lida=False
        )
        
        db.session.add(notificacao)
        db.session.commit()
        
        # Enviar notificação por email (opcional)
        usuario = Usuario.query.get(usuario_id)
        if usuario and usuario.email:
            enviar_email_notificacao(usuario.email, titulo, mensagem)
        
        return True
        
    except Exception as e:
        print(f'Erro ao notificar usuário: {str(e)}')
        return False

def enviar_email_notificacao(email, titulo, mensagem):
    """
    Envia um email de notificação.
    
    Args:
        email: Endereço de email do destinatário
        titulo: Título do email
        mensagem: Conteúdo do email
        
    Returns:
        Boolean indicando se o email foi enviado com sucesso
    """
    # Implementação simplificada, em produção seria integrado com um serviço de email
    try:
        print(f"Email enviado para {email}: {titulo} - {mensagem}")
        return True
    except Exception as e:
        print(f'Erro ao enviar email: {str(e)}')
        return False

def calcular_progresso_tarefa(tarefa):
    """
    Calcula o progresso de uma tarefa com base nas subtarefas.
    
    Args:
        tarefa: Objeto Tarefa para calcular o progresso
        
    Returns:
        Integer representando a porcentagem de conclusão (0-100)
    """
    if not tarefa.subtarefas:
        return 100 if tarefa.concluida else 0
    
    total_subtarefas = len(tarefa.subtarefas)
    subtarefas_concluidas = sum(1 for s in tarefa.subtarefas if s.concluida)
    
    if total_subtarefas == 0:
        return 0
    
    return int((subtarefas_concluidas / total_subtarefas) * 100)

def obter_estatisticas_tarefas(usuario_id):
    """
    Obtém estatísticas das tarefas de um usuário.
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        Dict contendo estatísticas das tarefas
    """
    from .task_models import Tarefa, ClassificacaoTarefa, StatusTarefa
    
    # Obter todas as tarefas do usuário
    tarefas = Tarefa.query.filter(
        (Tarefa.usuario_id == usuario_id) | 
        (Tarefa.responsavel_id == usuario_id)
    ).all()
    
    # Inicializar estatísticas
    estatisticas = {
        'total': len(tarefas),
        'concluidas': 0,
        'pendentes': 0,
        'em_andamento': 0,
        'atrasadas': 0,
        'por_classificacao': {
            'importancia': 0,
            'rotina': 0,
            'urgencia': 0,
            'pausa': 0
        },
        'por_prioridade': {
            'baixa': 0,
            'media': 0,
            'alta': 0,
            'critica': 0
        }
    }
    
    # Data atual para verificar atrasos
    data_atual = datetime.now()
    
    # Calcular estatísticas
    for tarefa in tarefas:
        # Status
        if tarefa.concluida:
            estatisticas['concluidas'] += 1
        elif tarefa.status == StatusTarefa.EM_ANDAMENTO:
            estatisticas['em_andamento'] += 1
        else:
            estatisticas['pendentes'] += 1
        
        # Verificar atraso
        if (not tarefa.concluida and 
            tarefa.data_prazo and 
            tarefa.data_prazo < data_atual):
            estatisticas['atrasadas'] += 1
        
        # Classificação
        classificacao = tarefa.classificacao.value
        estatisticas['por_classificacao'][classificacao] += 1
        
        # Prioridade
        prioridade = tarefa.prioridade.value
        estatisticas['por_prioridade'][prioridade] += 1
    
    return estatisticas

def obter_tarefas_proximas(usuario_id, dias=7):
    """
    Obtém tarefas com prazo próximo.
    
    Args:
        usuario_id: ID do usuário
        dias: Número de dias para considerar como próximo
        
    Returns:
        Lista de tarefas com prazo nos próximos dias
    """
    from .task_models import Tarefa
    
    # Data atual e limite
    data_atual = datetime.now()
    data_limite = data_atual + timedelta(days=dias)
    
    # Obter tarefas não concluídas com prazo nos próximos dias
    tarefas_proximas = Tarefa.query.filter(
        (Tarefa.usuario_id == usuario_id) | 
        (Tarefa.responsavel_id == usuario_id),
        Tarefa.concluida == False,
        Tarefa.data_prazo.isnot(None),
        Tarefa.data_prazo >= data_atual,
        Tarefa.data_prazo <= data_limite
    ).order_by(Tarefa.data_prazo).all()
    
    return tarefas_proximas
