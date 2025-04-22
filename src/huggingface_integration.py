"""
Integração com Hugging Face para o Agente de IA para Consultoria Educacional
Este módulo implementa a integração com modelos e serviços do Hugging Face.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union

import torch
import numpy as np
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering,
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BertForSequenceClassification,
    T5ForConditionalGeneration
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class HuggingFaceIntegration:
    """
    Classe para integração com modelos e serviços do Hugging Face.
    """
    
    def __init__(self, use_local_models=False, device="cpu"):
        """
        Inicializa a integração com Hugging Face.
        
        Args:
            use_local_models: Se True, usa modelos locais em vez de API
            device: Dispositivo para execução dos modelos ('cpu' ou 'cuda')
        """
        self.use_local_models = use_local_models
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        
        # Verificar disponibilidade de GPU
        if self.device == "cuda":
            logger.info(f"Usando GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.info("Usando CPU para inferência")
        
        # Inicializar modelos
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Inicializa os modelos necessários para o agente.
        """
        try:
            # Modelo para classificação de texto em português
            logger.info("Carregando modelo de classificação de texto...")
            model_name = "neuralmind/bert-base-portuguese-cased"
            self.tokenizers["text_classification"] = AutoTokenizer.from_pretrained(model_name)
            self.models["text_classification"] = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                num_labels=4  # Classificação para os 4 pilares
            ).to(self.device)
            
            # Modelo para perguntas e respostas em português
            logger.info("Carregando modelo de perguntas e respostas...")
            qa_model_name = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"
            self.pipelines["question_answering"] = pipeline(
                'question-answering', 
                model=qa_model_name, 
                tokenizer=qa_model_name,
                device=0 if self.device == "cuda" else -1
            )
            
            # Modelo para geração de texto em português
            logger.info("Carregando modelo de geração de texto...")
            gen_model_name = "unicamp-dl/ptt5-base-portuguese-vocab"
            self.tokenizers["text_generation"] = AutoTokenizer.from_pretrained(gen_model_name)
            self.models["text_generation"] = T5ForConditionalGeneration.from_pretrained(
                gen_model_name
            ).to(self.device)
            
            # Modelo para análise de sentimento em português
            logger.info("Carregando modelo de análise de sentimento...")
            sentiment_model_name = "neuralmind/bert-base-portuguese-cased"
            self.pipelines["sentiment_analysis"] = pipeline(
                'sentiment-analysis',
                model=sentiment_model_name,
                tokenizer=sentiment_model_name,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Todos os modelos carregados com sucesso!")
        
        except Exception as e:
            logger.error(f"Erro ao inicializar modelos: {str(e)}")
            raise
    
    def classify_text(self, text: str, labels: List[str]) -> Dict[str, float]:
        """
        Classifica um texto em categorias predefinidas.
        
        Args:
            text: Texto a ser classificado
            labels: Lista de rótulos possíveis
            
        Returns:
            Dicionário com probabilidades para cada rótulo
        """
        try:
            tokenizer = self.tokenizers["text_classification"]
            model = self.models["text_classification"]
            
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Converter logits para probabilidades
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().cpu().numpy()
            
            # Mapear probabilidades para rótulos
            result = {label: float(prob) for label, prob in zip(labels, probs)}
            return result
        
        except Exception as e:
            logger.error(f"Erro na classificação de texto: {str(e)}")
            # Retornar distribuição uniforme em caso de erro
            return {label: 1.0 / len(labels) for label in labels}
    
    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """
        Responde a uma pergunta com base em um contexto.
        
        Args:
            question: Pergunta a ser respondida
            context: Texto de contexto para encontrar a resposta
            
        Returns:
            Dicionário com a resposta e score de confiança
        """
        try:
            qa_pipeline = self.pipelines["question_answering"]
            result = qa_pipeline(question=question, context=context)
            return result
        
        except Exception as e:
            logger.error(f"Erro ao responder pergunta: {str(e)}")
            return {"answer": "Não foi possível encontrar uma resposta para esta pergunta.", "score": 0.0}
    
    def generate_text(self, prompt: str, max_length: int = 150) -> str:
        """
        Gera texto a partir de um prompt.
        
        Args:
            prompt: Texto inicial para geração
            max_length: Comprimento máximo do texto gerado
            
        Returns:
            Texto gerado
        """
        try:
            tokenizer = self.tokenizers["text_generation"]
            model = self.models["text_generation"]
            
            inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(self.device)
            
            # Configurações para geração de texto
            gen_kwargs = {
                "max_length": max_length,
                "num_beams": 5,
                "no_repeat_ngram_size": 2,
                "early_stopping": True,
                "do_sample": True,
                "top_k": 50,
                "top_p": 0.95,
                "temperature": 0.7
            }
            
            # Gerar texto
            with torch.no_grad():
                output_sequences = model.generate(**inputs, **gen_kwargs)
            
            # Decodificar o texto gerado
            generated_text = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
            return generated_text
        
        except Exception as e:
            logger.error(f"Erro na geração de texto: {str(e)}")
            return "Não foi possível gerar texto a partir do prompt fornecido."
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analisa o sentimento de um texto.
        
        Args:
            text: Texto para análise de sentimento
            
        Returns:
            Dicionário com rótulo de sentimento e score
        """
        try:
            sentiment_pipeline = self.pipelines["sentiment_analysis"]
            result = sentiment_pipeline(text)[0]
            return result
        
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {str(e)}")
            return {"label": "NEUTRAL", "score": 0.5}
    
    def process_educational_query(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa uma consulta educacional, integrando diferentes modelos.
        
        Args:
            query: Consulta em linguagem natural
            context: Contexto opcional para a consulta
            
        Returns:
            Dicionário com resposta, referências e sugestões
        """
        # Classificar a consulta nos pilares estratégicos
        pilares = ["pedagogico", "comercial", "marketing", "financeiro"]
        pilar_probs = self.classify_text(query, pilares)
        
        # Identificar o pilar principal
        pilar_principal = max(pilar_probs, key=pilar_probs.get)
        
        # Base de conhecimento específica para cada pilar
        knowledge_base = {
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
        
        # Usar o contexto fornecido ou o conhecimento do pilar principal
        effective_context = context if context else knowledge_base[pilar_principal]
        
        # Responder à consulta
        answer_result = self.answer_question(query, effective_context)
        
        # Gerar sugestões de seguimento
        follow_up_prompt = f"Gere três perguntas de seguimento sobre {pilar_principal} em consultoria educacional:"
        follow_up_suggestions = self.generate_text(follow_up_prompt, max_length=200)
        
        # Formatar sugestões como lista
        suggestions = [s.strip() for s in follow_up_suggestions.split("?") if s.strip()]
        suggestions = [f"{s}?" for s in suggestions[:3]]  # Limitar a 3 sugestões
        
        # Referências relevantes para cada pilar
        references = {
            "pedagogico": [
                "Placco, V. M. N. S., & Almeida, L. R. (2012). O coordenador pedagógico e os desafios da educação.",
                "Warschauer, C. (2017). Rodas e narrativas: caminhos para a autoria de pensamento."
            ],
            "comercial": [
                "Kotler, P., & Fox, K. F. (1994). Marketing estratégico para instituições educacionais."
            ],
            "marketing": [
                "Cobra, M., & Braga, R. (2004). Marketing educacional: ferramentas de gestão para instituições de ensino."
            ],
            "financeiro": [
                "Drucker, P. F. (1990). Managing the non-profit organization: Principles and practices."
            ]
        }
        
        # Montar resposta final
        result = {
            "resposta": answer_result["answer"],
            "confianca": float(answer_result["score"]),
            "pilar_principal": pilar_principal,
            "distribuicao_pilares": pilar_probs,
            "referencias": references[pilar_principal],
            "sugestoes_seguimento": suggestions
        }
        
        return result
    
    def create_huggingface_demo(self, demo_path: str = "demo") -> str:
        """
        Cria arquivos para demonstração no Hugging Face Spaces.
        
        Args:
            demo_path: Caminho para salvar os arquivos da demo
            
        Returns:
            Caminho para o arquivo principal da demo
        """
        try:
            os.makedirs(demo_path, exist_ok=True)
            
            # Criar arquivo app.py para Gradio
            app_py = """
import gradio as gr
import numpy as np
import pandas as pd
import json
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering

# Carregar modelos
@gr.on_load
def load_models():
    global qa_model, tokenizer
    model_name = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"
    qa_model = pipeline('question-answering', model=model_name, tokenizer=model_name)
    return qa_model

# Base de conhecimento
knowledge_base = {
    "pedagogico": \"\"\"
    O pilar pedagógico foca nas três dimensões do coordenador pedagógico: articuladora, formadora e transformadora.
    A dimensão articuladora conecta diferentes atores e saberes dentro da instituição educacional.
    A dimensão formadora promove o desenvolvimento profissional contínuo dos educadores.
    A dimensão transformadora catalisa mudanças nas concepções e práticas educacionais.
    As Rodas de Conversa são espaços de diálogo que favorecem a autoria de pensamento.
    A gestão construtivista valoriza a construção ativa do conhecimento e a autonomia.
    \"\"\",
    
    "comercial": \"\"\"
    O pilar comercial trata da captação e retenção de alunos de forma alinhada com os valores educacionais.
    A captação deve ser baseada em uma comunicação transparente e ética dos diferenciais pedagógicos.
    A retenção deve ser centrada na qualidade da experiência educacional oferecida.
    A precificação deve equilibrar sustentabilidade financeira e compromisso social.
    \"\"\",
    
    "marketing": \"\"\"
    O pilar de marketing cuida da comunicação e relacionamento com a comunidade.
    A comunicação deve ser educativa, explicando a abordagem pedagógica da instituição.
    O relacionamento com a comunidade deve ser baseado em engajamento genuíno.
    O posicionamento deve ser baseado em valores educacionais autênticos.
    \"\"\",
    
    "financeiro": \"\"\"
    O pilar financeiro busca a sustentabilidade institucional a serviço do projeto pedagógico.
    A gestão financeira deve estar alinhada com as prioridades pedagógicas.
    Os investimentos em formação continuada são estratégicos para a qualidade educacional.
    A sustentabilidade institucional requer equilíbrio entre impacto social e viabilidade econômica.
    \"\"\"
}

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

# Função para processar consultas
def process_query(query, history):
    # Identificar o pilar mais relevante
    pilares = ["pedagogico", "comercial", "marketing", "financeiro"]
    pilar_scores = {}
    
    for pilar in pilares:
        # Contagem simples de palavras-chave
        keywords = knowledge_base[pilar].lower().split()
        score = sum(1 for word in query.lower().split() if word in keywords)
        pilar_scores[pilar] = score
    
    # Selecionar o pilar com maior pontuação
    pilar_principal = max(pilar_scores, key=pilar_scores.get)
    
    # Se a pontuação for muito baixa, usar resposta genérica
    if pilar_scores[pilar_principal] <= 1:
        return "Posso ajudar com informações sobre os quatro pilares estratégicos: pedagógico, comercial, marketing e financeiro. Por favor, elabore sua pergunta com mais detalhes."
    
    # Usar o modelo de QA para gerar uma resposta
    try:
        context = knowledge_base[pilar_principal]
        result = qa_model(question=query, context=context)
        resposta = result['answer']
        
        # Adicionar informações sobre o pilar
        resposta += f"\\n\\nEsta resposta está relacionada principalmente ao pilar {pilar_principal}."
        
        return resposta
    except Exception as e:
        return f"Desculpe, ocorreu um erro ao processar sua consulta: {str(e)}"

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
        output = f"## Diagnóstico para Instituição #{instituicao_id}\\n\\n"
        
        for pilar in pilares_list:
            output += f"### Pilar {pilar.capitalize()}\\n\\n"
            
            # Métricas
            output += "#### Métricas\\n\\n"
            for metrica, valor in filtered_resultados[pilar].items():
                output += f"- {metrica.replace('_', ' ').capitalize()}: {valor*100:.1f}%\\n"
            
            # Recomendações
            output += "\\n#### Recomendações\\n\\n"
            for rec in filtered_recomendacoes[pilar]:
                output += f"- {rec}\\n"
            
            output += "\\n"
        
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
            output = f"## Simulação: Implementação de Nova Metodologia Pedagógica\\n\\n"
            output += f"### Instituição #{instituicao_id} - Horizonte: {horizonte} meses\\n\\n"
            output += "### Resultados Projetados\\n\\n"
            output += df.to_markdown(index=False)
            
            output += "\\n\\n### Análise\\n\\n"
            output += "- **Engajamento dos Alunos**: Crescimento consistente ao longo do período.\\n"
            output += "- **Satisfação dos Professores**: Queda inicial durante adaptação, seguida de crescimento significativo.\\n"
            output += "- **Resultados Acadêmicos**: Estabilidade inicial seguida de melhoria gradual.\\n\\n"
            
            output += "### Recomendações\\n\\n"
            output += "1. Implementar a metodologia em fases para minimizar o impacto inicial na satisfação dos professores.\\n"
            output += "2. Oferecer suporte intensivo nos primeiros 3 meses para acelerar a adaptação.\\n"
            output += "3. Comunicar às famílias que os resultados acadêmicos podem estabilizar antes de melhorar.\\n"
            
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
            output = f"## Simulação: Nova Estratégia Comercial\\n\\n"
            output += f"### Instituição #{instituicao_id} - Horizonte: {horizonte} meses\\n\\n"
            output += "### Resultados Projetados\\n\\n"
            output += df.to_markdown(index=False)
            
            output += "\\n\\n### Análise\\n\\n"
            output += "- **Taxa de Conversão**: Aumento significativo nos primeiros meses, seguido de estabilização.\\n"
            output += "- **Ticket Médio**: Crescimento gradual e consistente.\\n"
            output += "- **Taxa de Renovação**: Melhoria gradual, aproximando-se do limite teórico.\\n\\n"
            
            output += "### Recomendações\\n\\n"
            output += "1. Focar inicialmente na conversão de leads para capitalizar o rápido crescimento inicial.\\n"
            output += "2. Implementar estratégias de upsell a partir do 3º mês para maximizar o ticket médio.\\n"
            output += "3. Desenvolver programa de fidelização para sustentar a alta taxa de renovação.\\n"
            
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
            bot_message = process_query(message, chat_history)
            chat_history.append((message, bot_message))
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
        gr.Markdown(\"\"\"
        ## Agente de IA para Consultoria Educacional
        
        Este é um protótipo demonstrativo do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais.
        
        ### Funcionalidades
        
        - **Assistente Virtual**: Responde a perguntas sobre os quatro pilares estratégicos da consultoria educacional.
        - **Diagnóstico Institucional**: Gera diagnósticos personalizados para instituições educacionais.
        - **Simulação de Cenários**: Projeta resultados de diferentes intervenções ao longo do tempo.
        
        ### Limitações da Demo
        
        Esta demonstração utiliza dados simulados e tem funcionalidades limitadas em comparação com a versão completa do sistema.
        
        ### Contato
        
        Para mais informações, entre em contato com a Serra Projetos Educacionais.
        \"\"\")

# Iniciar a demo
if __name__ == "__main__":
    demo.launch()
            """
            
            with open(os.path.join(demo_path, "app.py"), "w") as f:
                f.write(app_py.strip())
            
            # Criar arquivo requirements.txt
            requirements = """
gradio>=3.50.2
numpy>=1.24.0
pandas>=2.0.0
transformers>=4.30.0
torch>=2.0.0
tabulate>=0.9.0
            """
            
            with open(os.path.join(demo_path, "requirements.txt"), "w") as f:
                f.write(requirements.strip())
            
            # Criar arquivo README.md
            readme = """
# Agente de IA para Consultoria Educacional - Demo

Esta é uma demonstração do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais.

## Funcionalidades

- **Assistente Virtual**: Responde a perguntas sobre os quatro pilares estratégicos da consultoria educacional.
- **Diagnóstico Institucional**: Gera diagnósticos personalizados para instituições educacionais.
- **Simulação de Cenários**: Projeta resultados de diferentes intervenções ao longo do tempo.

## Como usar

1. Acesse a aba "Assistente Virtual" para fazer perguntas sobre consultoria educacional.
2. Acesse a aba "Diagnóstico Institucional" para gerar diagnósticos para instituições.
3. Acesse a aba "Simulação de Cenários" para projetar resultados de diferentes intervenções.

## Limitações

Esta demonstração utiliza dados simulados e tem funcionalidades limitadas em comparação com a versão completa do sistema.
            """
            
            with open(os.path.join(demo_path, "README.md"), "w") as f:
                f.write(readme.strip())
            
            logger.info(f"Demo criada com sucesso em {demo_path}")
            return os.path.join(demo_path, "app.py")
        
        except Exception as e:
            logger.error(f"Erro ao criar demo: {str(e)}")
            raise

# Exemplo de uso
if __name__ == "__main__":
    # Inicializar integração
    hf_integration = HuggingFaceIntegration(use_local_models=True)
    
    # Testar classificação de texto
    text = "Como podemos melhorar a formação continuada dos professores?"
    labels = ["pedagogico", "comercial", "marketing", "financeiro"]
    result = hf_integration.classify_text(text, labels)
    print(f"Classificação: {result}")
    
    # Testar resposta a perguntas
    question = "Qual é o papel do coordenador pedagógico?"
    context = "O coordenador pedagógico desempenha três dimensões fundamentais: articuladora, formadora e transformadora."
    result = hf_integration.answer_question(question, context)
    print(f"Resposta: {result}")
    
    # Testar processamento de consulta educacional
    query = "Como implementar rodas de conversa na formação docente?"
    result = hf_integration.process_educational_query(query)
    print(f"Processamento de consulta: {result}")
    
    # Criar demo para Hugging Face Spaces
    demo_path = hf_integration.create_huggingface_demo("demo")
    print(f"Demo criada em: {demo_path}")
