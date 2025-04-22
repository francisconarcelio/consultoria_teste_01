"""
Backend principal do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais
Este módulo implementa a API principal e os serviços de backend do sistema.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Union

# FastAPI para API RESTful
from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Autenticação e segurança
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Processamento de dados
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Integração com Hugging Face
import torch
from transformers import (
    AutoModelForSequenceClassification, 
    AutoModelForQuestionAnswering,
    AutoTokenizer, 
    pipeline
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Agente de IA para Consultoria Educacional",
    description="API do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "chave_temporaria_para_desenvolvimento")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos de dados
class User(BaseModel):
    username: str
    email: str
    full_name: str
    disabled: bool = False
    role: str = "consultor"  # consultor, admin, gestor

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class InstituicaoEducacional(BaseModel):
    id: Optional[int] = None
    nome: str
    tipo: str  # escola, universidade, etc.
    segmento: str  # infantil, fundamental, médio, superior
    num_alunos: int
    num_professores: int
    localizacao: str
    data_cadastro: Optional[datetime] = None

class DadosAcademicos(BaseModel):
    instituicao_id: int
    periodo: str  # semestre, ano
    metricas: Dict[str, Any]  # notas, frequência, etc.
    segmentacao: Optional[Dict[str, Any]] = None

class DiagnosticoRequest(BaseModel):
    instituicao_id: int
    pilares: List[str] = ["pedagogico", "comercial", "marketing", "financeiro"]
    contexto: Optional[Dict[str, Any]] = None

class DiagnosticoResponse(BaseModel):
    instituicao_id: int
    timestamp: datetime
    resultados: Dict[str, Any]
    recomendacoes: Dict[str, List[str]]

class SimulacaoRequest(BaseModel):
    instituicao_id: int
    cenario: str
    parametros: Dict[str, Any]
    horizonte_temporal: int  # meses

class SimulacaoResponse(BaseModel):
    instituicao_id: int
    cenario: str
    resultados: Dict[str, Any]
    comparativo: Optional[Dict[str, Any]] = None

class ConsultaRequest(BaseModel):
    texto: str
    contexto: Optional[Dict[str, Any]] = None
    historico: Optional[List[Dict[str, str]]] = None

class ConsultaResponse(BaseModel):
    resposta: str
    referencias: Optional[List[str]] = None
    sugestoes_seguimento: Optional[List[str]] = None

# Banco de dados simulado (para demo)
fake_users_db = {
    "consultor": {
        "username": "consultor",
        "email": "consultor@serraprojetos.edu.br",
        "full_name": "Consultor Demonstração",
        "hashed_password": pwd_context.hash("senha123"),
        "disabled": False,
        "role": "consultor"
    },
    "admin": {
        "username": "admin",
        "email": "admin@serraprojetos.edu.br",
        "full_name": "Administrador Sistema",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
        "role": "admin"
    }
}

fake_instituicoes_db = {
    1: {
        "id": 1,
        "nome": "Escola Modelo",
        "tipo": "escola",
        "segmento": "fundamental",
        "num_alunos": 500,
        "num_professores": 30,
        "localizacao": "São Paulo, SP",
        "data_cadastro": datetime.now() - timedelta(days=180)
    },
    2: {
        "id": 2,
        "nome": "Colégio Inovação",
        "tipo": "escola",
        "segmento": "medio",
        "num_alunos": 350,
        "num_professores": 25,
        "localizacao": "Rio de Janeiro, RJ",
        "data_cadastro": datetime.now() - timedelta(days=90)
    }
}

# Funções de autenticação e segurança
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

# Carregamento dos modelos de IA
@app.on_event("startup")
async def startup_event():
    logger.info("Carregando modelos de IA...")
    
    global nlp_model, qa_model, tokenizer
    
    # Modelo para processamento de linguagem natural
    model_name = "neuralmind/bert-base-portuguese-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    nlp_model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # Modelo para perguntas e respostas
    qa_model_name = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"
    qa_model = pipeline('question-answering', model=qa_model_name, tokenizer=qa_model_name)
    
    logger.info("Modelos de IA carregados com sucesso!")

# Rotas de autenticação
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Rotas da API
@app.get("/")
async def root():
    return {"message": "Bem-vindo à API do Agente de IA para Consultoria Educacional da Serra Projetos Educacionais"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/instituicoes/", response_model=List[InstituicaoEducacional])
async def listar_instituicoes(current_user: User = Depends(get_current_active_user)):
    return [InstituicaoEducacional(**inst) for inst in fake_instituicoes_db.values()]

@app.get("/instituicoes/{instituicao_id}", response_model=InstituicaoEducacional)
async def obter_instituicao(
    instituicao_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    if instituicao_id not in fake_instituicoes_db:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")
    return InstituicaoEducacional(**fake_instituicoes_db[instituicao_id])

@app.post("/diagnostico/", response_model=DiagnosticoResponse)
async def realizar_diagnostico(
    request: DiagnosticoRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Realiza um diagnóstico institucional com base nos pilares selecionados.
    """
    # Verificar se a instituição existe
    if request.instituicao_id not in fake_instituicoes_db:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")
    
    # Simulação de processamento de diagnóstico
    resultados = {}
    recomendacoes = {}
    
    # Diagnóstico do pilar pedagógico
    if "pedagogico" in request.pilares:
        resultados["pedagogico"] = {
            "coerencia_ppp": 0.75,  # 75% de coerência
            "integracao_curricular": 0.68,
            "desenvolvimento_profissional": 0.82,
            "praticas_avaliativas": 0.65
        }
        recomendacoes["pedagogico"] = [
            "Implementar rodas de conversa semanais para fortalecer a integração curricular",
            "Desenvolver um programa de formação continuada baseado nas narrativas docentes",
            "Revisar as práticas avaliativas para maior alinhamento com a abordagem construtivista"
        ]
    
    # Diagnóstico do pilar comercial
    if "comercial" in request.pilares:
        resultados["comercial"] = {
            "taxa_conversao": 0.22,  # 22% de conversão
            "taxa_renovacao": 0.85,  # 85% de renovação
            "satisfacao_clientes": 0.78
        }
        recomendacoes["comercial"] = [
            "Alinhar o discurso comercial com os valores pedagógicos da instituição",
            "Implementar programa de embaixadores para aumentar indicações",
            "Desenvolver material de comunicação que destaque os diferenciais pedagógicos"
        ]
    
    # Diagnóstico do pilar de marketing
    if "marketing" in request.pilares:
        resultados["marketing"] = {
            "engajamento_redes": 0.45,
            "percepcao_marca": 0.72,
            "eficacia_campanhas": 0.58
        }
        recomendacoes["marketing"] = [
            "Criar conteúdo educativo que demonstre a abordagem pedagógica da instituição",
            "Desenvolver estratégia de comunicação baseada em histórias de transformação",
            "Implementar programa de relacionamento com a comunidade local"
        ]
    
    # Diagnóstico do pilar financeiro
    if "financeiro" in request.pilares:
        resultados["financeiro"] = {
            "sustentabilidade": 0.68,
            "eficiencia_operacional": 0.75,
            "investimento_formacao": 0.42
        }
        recomendacoes["financeiro"] = [
            "Aumentar o investimento em formação continuada dos educadores",
            "Otimizar processos administrativos para reduzir custos operacionais",
            "Desenvolver fontes alternativas de receita alinhadas com a missão institucional"
        ]
    
    return DiagnosticoResponse(
        instituicao_id=request.instituicao_id,
        timestamp=datetime.now(),
        resultados=resultados,
        recomendacoes=recomendacoes
    )

@app.post("/simulacao/", response_model=SimulacaoResponse)
async def simular_cenario(
    request: SimulacaoRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Simula um cenário específico para uma instituição educacional.
    """
    # Verificar se a instituição existe
    if request.instituicao_id not in fake_instituicoes_db:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")
    
    # Simulação de processamento de cenário
    resultados = {}
    comparativo = {}
    
    # Cenário: implementação de nova metodologia pedagógica
    if request.cenario == "nova_metodologia":
        # Simulação de resultados ao longo do tempo
        meses = list(range(1, request.horizonte_temporal + 1))
        
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
        
        # Impacto na percepção dos pais (melhoria gradual)
        percepcao_pais_base = 0.68
        percepcao_pais = [percepcao_pais_base + (0.15 * (1 - np.exp(-0.25 * m))) for m in meses]
        
        # Compilar resultados
        resultados = {
            "meses": meses,
            "engajamento_alunos": engajamento_crescimento,
            "satisfacao_professores": satisfacao_prof,
            "resultados_academicos": resultados_acad,
            "percepcao_pais": percepcao_pais
        }
        
        # Comparativo com cenário sem mudança
        comparativo = {
            "meses": meses,
            "engajamento_alunos": [engajamento_base] * len(meses),
            "satisfacao_professores": [satisfacao_prof_base] * len(meses),
            "resultados_academicos": [resultados_acad_base] * len(meses),
            "percepcao_pais": [percepcao_pais_base] * len(meses)
        }
    
    # Cenário: implementação de nova estratégia comercial
    elif request.cenario == "estrategia_comercial":
        # Simulação de resultados ao longo do tempo
        meses = list(range(1, request.horizonte_temporal + 1))
        
        # Impacto na taxa de conversão (crescimento rápido inicial, depois estabilização)
        conversao_base = 0.22
        conversao = [conversao_base + (0.15 * (1 - np.exp(-0.5 * m))) for m in meses]
        
        # Impacto no ticket médio (crescimento gradual)
        ticket_base = 1.0  # normalizado
        ticket = [ticket_base + (0.1 * (1 - np.exp(-0.2 * m))) for m in meses]
        
        # Impacto na taxa de renovação (melhoria gradual)
        renovacao_base = 0.85
        renovacao = [min(0.98, renovacao_base + (0.1 * (1 - np.exp(-0.15 * m)))) for m in meses]
        
        # Compilar resultados
        resultados = {
            "meses": meses,
            "taxa_conversao": conversao,
            "ticket_medio": ticket,
            "taxa_renovacao": renovacao
        }
        
        # Comparativo com cenário sem mudança
        comparativo = {
            "meses": meses,
            "taxa_conversao": [conversao_base] * len(meses),
            "ticket_medio": [ticket_base] * len(meses),
            "taxa_renovacao": [renovacao_base] * len(meses)
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Cenário '{request.cenario}' não implementado")
    
    return SimulacaoResponse(
        instituicao_id=request.instituicao_id,
        cenario=request.cenario,
        resultados=resultados,
        comparativo=comparativo
    )

@app.post("/consulta/", response_model=ConsultaResponse)
async def realizar_consulta(
    request: ConsultaRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Processa uma consulta em linguagem natural e retorna uma resposta contextualizada.
    """
    # Base de conhecimento simplificada para demo
    knowledge_base = {
        "coordenador_pedagogico": """
        O coordenador pedagógico desempenha três dimensões fundamentais: articuladora, formadora e transformadora.
        Como articulador, conecta diferentes atores e saberes dentro da instituição educacional.
        Como formador, promove o desenvolvimento profissional contínuo dos educadores.
        Como transformador, catalisa mudanças nas concepções e práticas educacionais.
        """,
        
        "rodas_conversa": """
        As Rodas de Conversa são espaços de diálogo e construção coletiva que favorecem a autoria de pensamento.
        Baseadas nas ideias de Cecília Warschauer, as Rodas promovem a integração de diferentes saberes e perspectivas.
        São ferramentas poderosas para formação continuada e desenvolvimento profissional dos educadores.
        """,
        
        "gestao_construtivista": """
        A gestão construtivista, baseada nos princípios de Piaget, valoriza a construção ativa do conhecimento.
        Promove a autonomia, a participação coletiva nos processos decisórios e o protagonismo dos educandos.
        Busca coerência entre os princípios pedagógicos e as práticas de gestão em todos os níveis.
        """,
        
        "pilares_estrategicos": """
        Os quatro pilares estratégicos da consultoria educacional são: Pedagógico, Comercial, Marketing e Financeiro.
        O pilar Pedagógico foca na qualidade dos processos educacionais e no desenvolvimento integral dos educandos.
        O pilar Comercial trata da captação e retenção de alunos de forma alinhada com os valores educacionais.
        O pilar de Marketing cuida da comunicação e relacionamento com a comunidade.
        O pilar Financeiro busca a sustentabilidade institucional a serviço do projeto pedagógico.
        """
    }
    
    # Processar a consulta
    query = request.texto.lower()
    
    # Identificar o tópico mais relevante
    best_topic = None
    best_score = -1
    
    for topic, content in knowledge_base.items():
        # Cálculo simplificado de relevância baseado em palavras-chave
        score = sum(1 for word in query.split() if word in content.lower())
        if score > best_score:
            best_score = score
            best_topic = topic
    
    # Se não encontrou um tópico relevante, usar resposta genérica
    if best_score <= 1:
        resposta = "Posso ajudar com informações sobre coordenação pedagógica, rodas de conversa, gestão construtivista e os quatro pilares estratégicos da consultoria educacional. Por favor, elabore sua pergunta com mais detalhes."
        sugestoes = [
            "Como o coordenador pedagógico pode atuar como articulador?",
            "Quais são os benefícios das Rodas de Conversa na formação docente?",
            "Como implementar uma gestão construtivista?",
            "Como integrar os quatro pilares estratégicos?"
        ]
        return ConsultaResponse(
            resposta=resposta,
            sugestoes_seguimento=sugestoes
        )
    
    # Usar o modelo de QA para gerar uma resposta contextualizada
    try:
        context = knowledge_base[best_topic]
        result = qa_model(question=request.texto, context=context)
        resposta = result['answer']
        
        # Adicionar informações complementares
        if best_topic == "coordenador_pedagogico":
            referencias = ["Placco, V. M. N. S., & Almeida, L. R. (2012). O coordenador pedagógico e os desafios da educação."]
            sugestoes = ["Como implementar as três dimensões na prática?", "Quais são os principais desafios do coordenador pedagógico?"]
        elif best_topic == "rodas_conversa":
            referencias = ["Warschauer, C. (2017). Rodas e narrativas: caminhos para a autoria de pensamento."]
            sugestoes = ["Como estruturar uma Roda de Conversa efetiva?", "Quais temas são mais produtivos para Rodas de Conversa?"]
        elif best_topic == "gestao_construtivista":
            referencias = ["Lima, A. O. (2002). Fazer escola: a gestão de uma escola piagetiana construtivista."]
            sugestoes = ["Como alinhar a gestão administrativa com princípios construtivistas?", "Quais indicadores avaliam uma gestão construtivista?"]
        else:  # pilares_estrategicos
            referencias = ["Documentação interna da Serra Projetos Educacionais"]
            sugestoes = ["Como integrar os quatro pilares na prática?", "Qual pilar deve ser priorizado em uma instituição em crise?"]
        
        return ConsultaResponse(
            resposta=resposta,
            referencias=referencias,
            sugestoes_seguimento=sugestoes
        )
    
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}")
        return ConsultaResponse(
            resposta="Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente com uma pergunta diferente.",
            sugestoes_seguimento=["Como o coordenador pedagógico pode atuar como articulador?", "Quais são os benefícios das Rodas de Conversa?"]
        )

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Requisição {request.method} {request.url.path} processada em {process_time:.4f}s")
    return response

# Tratamento de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."}
    )

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
