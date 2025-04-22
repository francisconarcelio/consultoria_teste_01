"""
Demo do Agente de IA para Consultoria Educacional - Serra Projetos Educacionais
Este script cria uma demonstração interativa usando Gradio para o Hugging Face Spaces.
"""

import os
import json
import numpy as np
import pandas as pd
import gradio as gr
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Base de conhecimento para os pilares
KNOWLEDGE_BASE = {
    "pedagogico": """
    O pilar pedagógico foca nas três dimensões do coordenador pedagógico: articuladora, formadora e transformadora.
    A dimensão articuladora conecta diferentes atores e saberes dentro da instituição educacional.
    A dimensão formadora promove o desenvolvimento profissional contínuo dos educadores.
    A dimensão transformadora catalisa mudanças nas concepções e práticas educacionais.
    As Rodas de Conversa são espaços de diálogo que favorecem a autoria de pensamento.
    A gestão construtivista valoriza a construção ativa do conhecimento e a autonomia.
    """,
    
    "comercial": """
    O pilar comercial trata da captação e retenção de alunos de forma alinhada com os valores educacionais.
    A captação deve ser baseada em uma comunicação transparente e ética dos diferenciais pedagógicos.
    A retenção deve ser centrada na qualidade da experiência educacional oferecida.
    A precificação deve equilibrar sustentabilidade financeira e compromisso social.
    """,
    
    "marketing": """
    O pilar de marketing cuida da comunicação e relacionamento com a comunidade.
    A comunicação deve ser educativa, explicando a abordagem pedagógica da instituição.
    O relacionamento com a comunidade deve ser baseado em engajamento genuíno.
    O posicionamento deve ser baseado em valores educacionais autênticos.
    """,
    
    "financeiro": """
    O pilar financeiro busca a sustentabilidade institucional a serviço do projeto pedagógico.
    A gestão financeira deve estar alinhada com as prioridades pedagógicas.
    Os investimentos em formação continuada são estratégicos para a qualidade educacional.
    A sustentabilidade institucional requer equilíbrio entre impacto social e viabilidade econômica.
    """
}

# Carregar modelos
qa_model = None

def load_models():
    global qa_model
    try:
        # Usar modelo de QA em português
        model_name = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"
        qa_model = pipeline('question-answering', model=model_name, tokenizer=model_name)
        return "Modelos carregados com sucesso!"
    except Exception as e:
        return f"Erro ao carregar modelos: {str(e)}"

# Função para processar consultas
def process_query(query, history):
    if not query:
        return history
    
    # Identificar o pilar mais relevante
    pilares = ["pedagogico", "comercial", "marketing", "financeiro"]
    pilar_scores = {}
    
    for pilar in pilares:
        # Contagem simples de palavras-chave
        keywords = KNOWLEDGE_BASE[pilar].lower().split()
        score = sum(1 for word in query.lower().split() if word in keywords)
        pilar_scores[pilar] = score
    
    # Selecionar o pilar com maior pontuação
    pilar_principal = max(pilar_scores, key=pilar_scores.get)
    
    # Se a pontuação for muito baixa, usar resposta genérica
    if pilar_scores[pilar_principal] <= 1:
        resposta = "Posso ajudar com informações sobre os quatro pilares estratégicos: pedagógico, comercial, marketing e financeiro. Por favor, elabore sua pergunta com mais detalhes."
    else:
        # Usar o modelo de QA para gerar uma resposta
        try:
            global qa_model
            if qa_model is None:
                load_models()
                
            context = KNOWLEDGE_BASE[pilar_principal]
            result = qa_model(question=query, context=context)
            resposta = result['answer']
            
            # Adicionar informações sobre o pilar
            resposta += f"\n\nEsta resposta está relacionada principalmente ao pilar {pilar_principal}."
        except Exception as e:
            resposta = f"Desculpe, ocorreu um erro ao processar sua consulta: {str(e)}"
    
    # Atualizar histórico
    history.append((query, resposta))
    return history

# Dados simulados para diagnóstico
def get_diagnostic_data(instituicao_id):
    # Dados simulados para demonstração
    resultados = {
        "pedagogico": {
            "coerencia_ppp": 0.75,
            "integracao_curricular": 0.68,
            "desenvolvimento_profissional": 0.82,
            "praticas_avaliativas": 0.65
        },
        "comercial": {
            "taxa_conversao": 0.22,
            "taxa_renovacao": 0.85,
            "satisfacao_clientes": 0.78
        },
        "marketing": {
            "engajamento_redes": 0.45,
            "percepcao_marca": 0.72,
            "eficacia_campanhas": 0.58
        },
        "financeiro": {
            "sustentabilidade": 0.68,
            "eficiencia_operacional": 0.75,
            "investimento_formacao": 0.42
        }
    }
    
    recomendacoes = {
        "pedagogico": [
            "Implementar rodas de conversa semanais para fortalecer a integração curricular",
            "Desenvolver um programa de formação continuada baseado nas narrativas docentes",
            "Revisar as práticas avaliativas para maior alinhamento com a abordagem construtivista"
        ],
        "comercial": [
            "Alinhar o discurso comercial com os valores pedagógicos da instituição",
            "Implementar programa de embaixadores para aumentar indicações",
            "Desenvolver material de comunicação que destaque os diferenciais pedagógicos"
        ],
        "marketing": [
            "Criar conteúdo educativo que demonstre a abordagem pedagógica da instituição",
            "Desenvolver estratégia de comunicação baseada em histórias de transformação",
            "Implementar programa de relacionamento com a comunidade local"
        ],
        "financeiro": [
            "Aumentar o investimento em formação continuada dos educadores",
            "Otimizar processos administrativos para reduzir custos operacionais",
            "Desenvolver fontes alternativas de receita alinhadas com a missão institucional"
        ]
    }
    
    return resultados, recomendacoes

# Função para gerar diagnóstico
def generate_diagnostic(instituicao_id, pilares):
    try:
        # Converter string de pilares em lista
        pilares_list = [p.strip() for p in pilares.split(",")]
        
        # Validar pilares
        valid_pilares = ["pedagogico", "comercial", "marketing", "financeiro"]
        pilares_list = [p for p in pilares_list if p in valid_pilares]
        
        if not pilares_list:
            return "Por favor, selecione pelo menos um pilar válido (pedagógico, comercial, marketing, financeiro)."
        
        # Obter dados de diagnóstico
        resultados, recomendacoes = get_diagnostic_data(instituicao_id)
        
        # Filtrar resultados para os pilares selecionados
        filtered_resultados = {p: resultados[p] for p in pilares_list if p in resultados}
        filtered_recomendacoes = {p: recomendacoes[p] for p in pilares_list if p in recomendacoes}
        
        # Formatar saída
        output = f"## Diagnóstico para Instituição #{instituicao_id}\n\n"
        
        for pilar in pilares_list:
            output += f"### Pilar {pilar.capitalize()}\n\n"
            
            # Métricas
            output += "#### Métricas\n\n"
            for metrica, valor in filtered_resultados[pilar].items():
                output += f"- {metrica.replace('_', ' ').capitalize()}: {valor*100:.1f}%\n"
            
            # Recomendações
            output += "\n#### Recomendações\n\n"
            for rec in filtered_recomendacoes[pilar]:
                output += f"- {rec}\n"
            
            output += "\n"
        
        return output
    
    except Exception as e:
        return f"Erro ao gerar diagnóstico: {str(e)}"

# Função para simular cenário
def simulate_scenario(instituicao_id, cenario, horizonte):
    try:
        # Validar cenário
        valid_cenarios = ["nova_metodologia", "estrategia_comercial"]
        if cenario not in valid_cenarios:
            return "Por favor, selecione um cenário válido (nova_metodologia, estrategia_comercial)."
        
        # Validar horizonte temporal
        horizonte = int(horizonte)
        if horizonte < 1 or horizonte > 24:
            return "O horizonte temporal deve estar entre 1 e 24 meses."
        
        # Simulação de cenário: implementação de nova metodologia pedagógica
        if cenario == "nova_metodologia":
            # Simulação de resultados ao longo do tempo
            meses = list(range(1, horizonte + 1))
            
            # Impacto no engajamento dos alunos (crescimento gradual)
            engajamento_base = 0.65
            engajamento_crescimento = [engajamento_base + (0.2 * (1 - np.exp(-0.3 * m))) for m in meses]
            
            # Impacto na satisfação dos professores (queda inicial, depois crescimento)
            satisfacao_prof_base = 0.75
            satisfacao_prof = [satisfacao_prof_base - 0.1 + (0.2 * (1 - np.exp(-0.2 * m))) for m in meses]
            
            # Impacto nos resultados acadêmicos (melhoria gradual após período de adaptação)
            resultados_acad_base = 0.7
            resultados_acad = [resultados_acad_base - 0.05 + (0.15 * (1 - np.exp(-0.15 * (m-2)))) for m in meses]
            resultados_acad = [max(resultados_acad_base, r) for r in resultados_acad]  # não cai abaixo da linha base
            
            # Criar DataFrame para visualização
            df = pd.DataFrame({
                'Mês': meses,
                'Engajamento dos Alunos': [f"{e*100:.1f}%" for e in engajamento_crescimento],
                'Satisfação dos Professores': [f"{s*100:.1f}%" for s in satisfacao_prof],
                'Resultados Acadêmicos': [f"{r*100:.1f}%" for r in resultados_acad]
            })
            
            # Formatar saída
            output = f"## Simulação: Implementação de Nova Metodologia Pedagógica\n\n"
            output += f"### Instituição #{instituicao_id} - Horizonte: {horizonte} meses\n\n"
            output += "### Resultados Projetados\n\n"
            output += df.to_markdown(index=False)
            
            output += "\n\n### Análise\n\n"
            output += "- **Engajamento dos Alunos**: Crescimento consistente ao longo do período.\n"
            output += "- **Satisfação dos Professores**: Queda inicial durante adaptação, seguida de crescimento significativo.\n"
            output += "- **Resultados Acadêmicos**: Estabilidade inicial seguida de melhoria gradual.\n\n"
            
            output += "### Recomendações\n\n"
            output += "1. Implementar a metodologia em fases para minimizar o impacto inicial na satisfação dos professores.\n"
            output += "2. Oferecer suporte intensivo nos primeiros 3 meses para acelerar a adaptação.\n"
            output += "3. Comunicar às famílias que os resultados acadêmicos podem estabilizar antes de melhorar.\n"
            
            return output
        
        # Cenário: implementação de nova estratégia comercial
        elif cenario == "estrategia_comercial":
            # Simulação de resultados ao longo do tempo
            meses = list(range(1, horizonte + 1))
            
            # Impacto na taxa de conversão (crescimento rápido inicial, depois estabilização)
            conversao_base = 0.22
            conversao = [conversao_base + (0.15 * (1 - np.exp(-0.5 * m))) for m in meses]
            
            # Impacto no ticket médio (crescimento gradual)
            ticket_base = 1.0  # normalizado
            ticket = [ticket_base + (0.1 * (1 - np.exp(-0.2 * m))) for m in meses]
            
            # Impacto na taxa de renovação (melhoria gradual)
            renovacao_base = 0.85
            renovacao = [min(0.98, renovacao_base + (0.1 * (1 - np.exp(-0.15 * m)))) for m in meses]
            
            # Criar DataFrame para visualização
            df = pd.DataFrame({
                'Mês': meses,
                'Taxa de Conversão': [f"{c*100:.1f}%" for c in conversao],
                'Ticket Médio (normalizado)': [f"{t:.2f}" for t in ticket],
                'Taxa de Renovação': [f"{r*100:.1f}%" for r in renovacao]
            })
            
            # Formatar saída
            output = f"## Simulação: Nova Estratégia Comercial\n\n"
            output += f"### Instituição #{instituicao_id} - Horizonte: {horizonte} meses\n\n"
            output += "### Resultados Projetados\n\n"
            output += df.to_markdown(index=False)
            
            output += "\n\n### Análise\n\n"
            output += "- **Taxa de Conversão**: Aumento significativo nos primeiros meses, seguido de estabilização.\n"
            output += "- **Ticket Médio**: Crescimento gradual e consistente.\n"
            output += "- **Taxa de Renovação**: Melhoria gradual, aproximando-se do limite teórico.\n\n"
            
            output += "### Recomendações\n\n"
            output += "1. Focar inicialmente na conversão de leads para capitalizar o rápido crescimento inicial.\n"
            output += "2. Implementar estratégias de upsell a partir do 3º mês para maximizar o ticket médio.\n"
            output += "3. Desenvolver programa de fidelização para sustentar a alta taxa de renovação.\n"
            
            return output
    
    except Exception as e:
        return f"Erro ao simular cenário: {str(e)}"

# Interface Gradio
with gr.Blocks(title="Agente de IA para Consultoria Educacional - Serra Projetos Educacionais") as demo:
    gr.Markdown("# Agente de IA para Consultoria Educacional")
    gr.Markdown("## Serra Projetos Educacionais")
    
    with gr.Tab("Assistente Virtual"):
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(label="Faça sua pergunta sobre consultoria educacional")
        clear = gr.Button("Limpar Conversa")
        
        def respond(message, chat_history):
            if not message:
                return "", chat_history
            chat_history = process_query(message, chat_history)
            return "", chat_history
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)
    
    with gr.Tab("Diagnóstico Institucional"):
        with gr.Row():
            instituicao_id = gr.Number(label="ID da Instituição", value=1, minimum=1, maximum=10, step=1)
            pilares = gr.Textbox(label="Pilares (separados por vírgula)", value="pedagogico, comercial, marketing, financeiro")
        
        diagnostico_btn = gr.Button("Gerar Diagnóstico")
        diagnostico_output = gr.Markdown()
        
        diagnostico_btn.click(generate_diagnostic, [instituicao_id, pilares], diagnostico_output)
    
    with gr.Tab("Simulação de Cenários"):
        with gr.Row():
            sim_instituicao_id = gr.Number(label="ID da Instituição", value=1, minimum=1, maximum=10, step=1)
            sim_cenario = gr.Dropdown(label="Cenário", choices=["nova_metodologia", "estrategia_comercial"], value="nova_metodologia")
            sim_horizonte = gr.Slider(label="Horizonte Temporal (meses)", minimum=1, maximum=24, value=12, step=1)
        
        simulacao_btn = gr.Button("Simular Cenário")
        simulacao_output = gr.Markdown()
        
        simulacao_btn.click(simulate_scenario, [sim_instituicao_id, sim_cenario, sim_horizonte], simulacao_output)
    
    with gr.Tab("Sobre"):
        gr.Markdown("""
        ## Agente de IA para Consultoria Educacional
        
        Este é um protótipo demonstrativo do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais.
        
        ### Funcionalidades
        
        - **Assistente Virtual**: Responde a perguntas sobre os quatro pilares estratégicos da consultoria educacional.
        - **Diagnóstico Institucional**: Gera diagnósticos personalizados para instituições educacionais.
        - **Simulação de Cenários**: Projeta resultados de diferentes intervenções ao longo do tempo.
        
        ### Abordagem Pedagógica
        
        O agente incorpora princípios da pedagogia construtivista e valoriza:
        
        - As três dimensões do coordenador pedagógico: articuladora, formadora e transformadora
        - Metodologias de Rodas de Conversa e Narrativas para formação continuada
        - Desenvolvimento da autoria de pensamento e autonomia
        - Gestão participativa e construção coletiva do conhecimento
        
        ### Limitações da Demo
        
        Esta demonstração utiliza dados simulados e tem funcionalidades limitadas em comparação com a versão completa do sistema.
        
        ### Contato
        
        Para mais informações, entre em contato com a Serra Projetos Educacionais.
        """)

# Carregar modelos ao iniciar
load_models()

# Iniciar a demo
if __name__ == "__main__":
    demo.launch()
