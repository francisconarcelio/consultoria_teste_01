# Documentação do Agente de IA para Consultoria Educacional - Serra Projetos Educacionais

## Visão Geral

O Agente de IA para Consultoria Educacional é uma solução tecnológica desenvolvida para a Serra Projetos Educacionais, com o objetivo de potencializar o trabalho de consultoria educacional através da integração de inteligência artificial. O sistema aborda os quatro pilares estratégicos da consultoria: Pedagógico, Comercial, Marketing e Financeiro, com ênfase especial na abordagem construtivista e nas três dimensões do coordenador pedagógico (articuladora, formadora e transformadora).

## Arquitetura do Sistema

O sistema foi desenvolvido com uma arquitetura em camadas que separa claramente as responsabilidades:

1. **Camada de Apresentação**: Interface web responsiva e demo no Hugging Face
2. **Camada de Aplicação**: API RESTful com FastAPI
3. **Camada de Domínio**: Lógica de negócio e processamento de IA
4. **Camada de Infraestrutura**: Integração com modelos do Hugging Face e banco de dados

## Componentes Principais

### Backend (backend.py)

O backend implementa uma API RESTful usando FastAPI, com as seguintes funcionalidades:

- Autenticação e autorização de usuários
- Endpoints para diagnóstico institucional
- Endpoints para simulação de cenários
- Endpoints para consultas em linguagem natural
- Integração com modelos de IA

#### Endpoints Principais

- `/auth/login`: Autenticação de usuários
- `/diagnostico/{instituicao_id}`: Geração de diagnóstico institucional
- `/simulacao/{instituicao_id}`: Simulação de cenários
- `/consulta`: Processamento de consultas em linguagem natural

### Integração com Hugging Face (huggingface_integration.py)

Este módulo implementa a integração com modelos e serviços do Hugging Face, incluindo:

- Classificação de texto para identificação de pilares
- Resposta a perguntas baseada em contexto
- Geração de texto para recomendações
- Análise de sentimento para feedback

#### Classes Principais

- `HuggingFaceIntegration`: Classe principal que gerencia a integração com os modelos
  - `classify_text()`: Classifica texto em categorias predefinidas
  - `answer_question()`: Responde perguntas com base em contexto
  - `generate_text()`: Gera texto a partir de prompts
  - `analyze_sentiment()`: Analisa sentimento de textos
  - `process_educational_query()`: Processa consultas educacionais
  - `create_huggingface_demo()`: Cria arquivos para demo no Hugging Face

### Frontend (index.html, styles.css, script.js)

O frontend implementa uma interface web responsiva com Bootstrap, incluindo:

- Dashboard com visão geral das instituições e atividades
- Módulo de diagnóstico institucional
- Módulo de simulação de cenários
- Assistente virtual para consultas em linguagem natural
- Gerenciamento de instituições

#### Componentes da Interface

- **Dashboard**: Visão geral com métricas e atividades recentes
- **Diagnóstico**: Formulário para geração de diagnósticos e visualização de resultados
- **Simulação**: Formulário para simulação de cenários e visualização de projeções
- **Assistente Virtual**: Chat interativo para consultas em linguagem natural
- **Instituições**: Gerenciamento de instituições educacionais

### Demo Hugging Face (app.py)

A demo implementa uma versão simplificada do sistema usando Gradio para o Hugging Face Spaces, incluindo:

- Assistente virtual para consultas sobre os pilares
- Diagnóstico institucional simplificado
- Simulação de cenários com visualização de resultados

## Medidas de Segurança

O sistema implementa diversas medidas de segurança:

- **Proteção contra XSS**: Sanitização de entrada de usuário
- **Proteção contra CSRF**: Tokens CSRF em requisições
- **Proteção contra Clickjacking**: Prevenção de embedding em iframes
- **Validação de Entrada**: Validação de todos os dados de formulários
- **Proteção de Sessão**: Timeout por inatividade e renovação de tokens

## Fundamentos Pedagógicos

O sistema incorpora princípios pedagógicos construtivistas e valoriza:

1. **As três dimensões do coordenador pedagógico**:
   - **Articuladora**: Conexão entre diferentes atores e saberes
   - **Formadora**: Desenvolvimento profissional contínuo dos educadores
   - **Transformadora**: Catalisação de mudanças nas concepções e práticas

2. **Metodologias de Rodas de Conversa e Narrativas**:
   - Espaços de diálogo que favorecem a autoria de pensamento
   - Documentação reflexiva dos processos educacionais

3. **Gestão Construtivista**:
   - Valorização da construção ativa do conhecimento
   - Autonomia e participação coletiva nos processos decisórios

## Guia de Instalação e Uso

### Requisitos

- Python 3.8+
- Node.js 14+
- Pip e NPM

### Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/serra-projetos/agente-ia-consultoria.git
   cd agente-ia-consultoria
   ```

2. Instale as dependências do backend:
   ```
   pip install -r requirements.txt
   ```

3. Instale as dependências do frontend:
   ```
   npm install
   ```

4. Configure as variáveis de ambiente:
   ```
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

5. Inicie o servidor:
   ```
   python backend.py
   ```

6. Acesse a aplicação em `http://localhost:8000`

### Uso da Demo no Hugging Face

1. Acesse a demo em `https://huggingface.co/spaces/serra-projetos/agente-ia-consultoria`
2. Utilize a aba "Assistente Virtual" para fazer perguntas sobre os pilares
3. Utilize a aba "Diagnóstico Institucional" para gerar diagnósticos
4. Utilize a aba "Simulação de Cenários" para projetar resultados de intervenções

## Limitações e Trabalhos Futuros

### Limitações Atuais

- A demo utiliza dados simulados para diagnósticos e simulações
- Os modelos de linguagem têm conhecimento limitado sobre contextos específicos
- A integração com sistemas existentes das instituições não está implementada

### Trabalhos Futuros

- Implementação de aprendizado contínuo com feedback dos consultores
- Integração com sistemas de gestão escolar
- Desenvolvimento de módulos específicos para cada segmento educacional
- Implementação de visualizações mais avançadas para análise de dados

## Referências

- Placco, V. M. N. S., & Almeida, L. R. (2012). O coordenador pedagógico e os desafios da educação.
- Warschauer, C. (2017). Rodas e narrativas: caminhos para a autoria de pensamento.
- Lima, A. O. Fazer escola: a gestão de uma escola piagetiana construtivista.
- Documentação do Hugging Face: https://huggingface.co/docs
- Documentação do FastAPI: https://fastapi.tiangolo.com/
- Documentação do Gradio: https://gradio.app/docs/
