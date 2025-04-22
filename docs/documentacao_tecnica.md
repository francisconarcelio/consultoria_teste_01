# Documentação Técnica - Sistema de Consultoria Educacional

## Sumário

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
3. [Módulos do Sistema](#módulos-do-sistema)
   - [Autenticação (auth)](#módulo-de-autenticação-auth)
   - [Gerenciamento de Arquivos (files)](#módulo-de-gerenciamento-de-arquivos-files)
   - [Sistema de Tarefas (tasks)](#módulo-de-sistema-de-tarefas-tasks)
   - [Dashboard Administrativo (admin)](#módulo-de-dashboard-administrativo-admin)
   - [Conformidade LGPD (lgpd)](#módulo-de-conformidade-lgpd-lgpd)
   - [Integração com Hugging Face](#módulo-de-integração-com-hugging-face)
4. [API e Endpoints](#api-e-endpoints)
5. [Segurança](#segurança)
6. [Integração com Serviços Externos](#integração-com-serviços-externos)
7. [Requisitos de Sistema](#requisitos-de-sistema)
8. [Guia de Instalação](#guia-de-instalação)
9. [Manutenção e Backup](#manutenção-e-backup)
10. [Solução de Problemas](#solução-de-problemas)

## Visão Geral da Arquitetura

O Sistema de Consultoria Educacional da Serra Projetos Educacionais é construído utilizando uma arquitetura modular baseada em Flask, um framework web leve e flexível para Python. A arquitetura segue o padrão MVC (Model-View-Controller) adaptado para aplicações Flask.

### Componentes Principais:

- **Backend**: Python 3.10+ com Flask 2.2+
- **ORM**: SQLAlchemy para mapeamento objeto-relacional
- **Frontend**: HTML5, CSS3, JavaScript com Bootstrap 5
- **Banco de Dados**: SQLite (desenvolvimento), PostgreSQL (produção)
- **Autenticação**: Flask-Login com suporte a OAuth 2.0
- **Armazenamento de Arquivos**: Sistema de arquivos local com abstração para migração para S3
- **Integração IA**: API Hugging Face para análise de texto e recomendações

### Diagrama de Arquitetura:

```
+----------------------------------+
|           Cliente                |
|  (Navegador Web / Dispositivo)   |
+----------------------------------+
               |
               | HTTP/HTTPS
               |
+----------------------------------+
|         Servidor Web             |
|      (Nginx / Gunicorn)          |
+----------------------------------+
               |
               | WSGI
               |
+----------------------------------+
|       Aplicação Flask            |
|                                  |
|  +-------------+  +------------+ |
|  | Blueprints  |  | Extensions | |
|  +-------------+  +------------+ |
|                                  |
|  +-------------+  +------------+ |
|  |   Models    |  |  Services  | |
|  +-------------+  +------------+ |
|                                  |
|  +-------------+  +------------+ |
|  |   Views     |  |   Utils    | |
|  +-------------+  +------------+ |
+----------------------------------+
               |
               |
+----------------------------------+
|         Banco de Dados           |
|      (SQLite / PostgreSQL)       |
+----------------------------------+
               |
               |
+----------------------------------+
|       Serviços Externos          |
| (Google API, Hugging Face, etc.) |
+----------------------------------+
```

## Estrutura do Banco de Dados

O sistema utiliza SQLAlchemy como ORM (Object-Relational Mapping) para interagir com o banco de dados. A estrutura do banco de dados é composta por várias tabelas que representam as entidades principais do sistema.

### Principais Tabelas:

#### Autenticação e Usuários:
- `usuarios`: Armazena informações dos usuários
- `perfil_usuario`: Define os diferentes perfis de acesso
- `tokens_recuperacao`: Tokens para recuperação de senha
- `logs_autenticacao`: Registros de login/logout
- `consentimento_lgpd`: Registros de consentimentos LGPD

#### Tarefas:
- `tarefas`: Tarefas principais do sistema
- `subtarefas`: Subtarefas associadas a tarefas principais
- `comentarios_tarefa`: Comentários em tarefas
- `projetos`: Projetos que agrupam tarefas
- `instituicoes`: Instituições associadas a projetos/tarefas
- `eventos_calendario`: Eventos sincronizados com Google Agenda

#### Arquivos:
- `arquivos`: Metadados de arquivos enviados
- `conteudo_arquivo`: Conteúdo binário dos arquivos (quando armazenados no BD)
- `versoes_arquivo`: Histórico de versões de arquivos

#### Administração:
- `logs_sistema`: Logs de atividades do sistema
- `configuracoes`: Configurações do sistema
- `estatisticas`: Estatísticas calculadas
- `notificacoes`: Notificações do sistema
- `backups`: Registros de backups realizados
- `relatorios_agendados`: Configurações de relatórios periódicos

### Diagrama ER:

O diagrama ER completo está disponível no arquivo `/docs/diagrama_er.png`.

### Índices e Otimizações:

- Índices em colunas frequentemente consultadas (IDs, emails, datas)
- Índices compostos para consultas de relacionamento
- Chaves estrangeiras com restrições de integridade referencial
- Otimização de consultas frequentes com índices específicos

## Módulos do Sistema

O sistema é dividido em módulos independentes (implementados como Blueprints do Flask), cada um responsável por um conjunto específico de funcionalidades.

### Módulo de Autenticação (auth)

Responsável pelo gerenciamento de usuários, autenticação e controle de acesso.

#### Principais Arquivos:
- `auth/__init__.py`: Inicialização do módulo
- `auth/auth_models.py`: Modelos de dados (Usuario, PerfilUsuario, etc.)
- `auth/auth_routes.py`: Rotas e controladores
- `auth/auth_forms.py`: Formulários de autenticação
- `auth/auth_utils.py`: Funções utilitárias

#### Funcionalidades:
- Registro de usuários
- Login/logout
- Recuperação de senha
- Perfis de usuário e permissões
- Autenticação OAuth (Google, Apple, Microsoft)
- Gerenciamento de perfil

### Módulo de Gerenciamento de Arquivos (files)

Responsável pelo upload, armazenamento e gerenciamento de arquivos.

#### Principais Arquivos:
- `files/__init__.py`: Inicialização do módulo
- `files/file_models.py`: Modelos de dados (Arquivo, ConteudoArquivo, etc.)
- `files/file_routes.py`: Rotas e controladores
- `files/file_utils.py`: Funções utilitárias para manipulação de arquivos

#### Funcionalidades:
- Upload de arquivos (PDF, DOC, TXT)
- Validação de tipos de arquivo
- Extração de texto de documentos
- Visualização de arquivos
- Download de arquivos
- Exclusão de arquivos

### Módulo de Sistema de Tarefas (tasks)

Responsável pelo gerenciamento de tarefas, subtarefas e classificação.

#### Principais Arquivos:
- `tasks/__init__.py`: Inicialização do módulo
- `tasks/task_models.py`: Modelos de dados (Tarefa, Subtarefa, etc.)
- `tasks/task_routes.py`: Rotas e controladores
- `tasks/task_utils.py`: Funções utilitárias

#### Funcionalidades:
- Criação e edição de tarefas
- Classificação (Importância, Rotina, Urgência, Pausa)
- Subtarefas
- Comentários
- Integração com Google Agenda
- Visualização Kanban

### Módulo de Dashboard Administrativo (admin)

Responsável pelo gerenciamento administrativo do sistema.

#### Principais Arquivos:
- `admin/__init__.py`: Inicialização do módulo
- `admin/admin_models.py`: Modelos de dados (LogSistema, Configuracao, etc.)
- `admin/admin_routes.py`: Rotas e controladores
- `admin/admin_utils.py`: Funções utilitárias

#### Funcionalidades:
- Gerenciamento de usuários
- Logs do sistema
- Configurações do sistema
- Backups
- Relatórios
- Estatísticas

### Módulo de Conformidade LGPD (lgpd)

Responsável pela conformidade com a Lei Geral de Proteção de Dados.

#### Principais Arquivos:
- `lgpd/__init__.py`: Inicialização do módulo e funções principais
- `lgpd/templates/`: Templates para políticas e formulários

#### Funcionalidades:
- Gerenciamento de consentimentos
- Políticas de privacidade e termos de uso
- Exportação de dados do usuário
- Solicitação de exclusão de dados
- Anonimização de dados
- Logs de acesso a dados pessoais

### Módulo de Integração com Hugging Face

Responsável pela integração com modelos de IA da Hugging Face.

#### Principais Arquivos:
- `huggingface_integration.py`: Funções de integração com a API

#### Funcionalidades:
- Análise de texto de documentos
- Classificação automática de tarefas
- Recomendações baseadas em conteúdo
- Extração de entidades e conceitos

## API e Endpoints

O sistema oferece uma API interna para comunicação entre o frontend e o backend. Os principais endpoints estão organizados por módulo.

### Autenticação:
- `POST /auth/login`: Autenticação de usuário
- `POST /auth/registro`: Registro de novo usuário
- `POST /auth/recuperar-senha`: Solicitação de recuperação de senha
- `GET /auth/perfil`: Obtenção de dados do perfil
- `PUT /auth/perfil`: Atualização de dados do perfil

### Tarefas:
- `GET /tasks/`: Listagem de tarefas
- `POST /tasks/`: Criação de nova tarefa
- `GET /tasks/<id>`: Obtenção de detalhes de tarefa
- `PUT /tasks/<id>`: Atualização de tarefa
- `DELETE /tasks/<id>`: Exclusão de tarefa
- `POST /tasks/<id>/subtarefas`: Adição de subtarefa
- `POST /tasks/<id>/comentarios`: Adição de comentário

### Arquivos:
- `GET /files/`: Listagem de arquivos
- `POST /files/`: Upload de arquivo
- `GET /files/<id>`: Obtenção de detalhes de arquivo
- `GET /files/<id>/download`: Download de arquivo
- `DELETE /files/<id>`: Exclusão de arquivo

### Administração:
- `GET /admin/usuarios`: Listagem de usuários
- `GET /admin/logs`: Listagem de logs
- `GET /admin/configuracoes`: Listagem de configurações
- `POST /admin/backups`: Criação de backup
- `POST /admin/relatorios`: Geração de relatório

### LGPD:
- `GET /lgpd/consent`: Obtenção de consentimentos
- `POST /lgpd/consent`: Atualização de consentimentos
- `GET /lgpd/data-export`: Exportação de dados
- `POST /lgpd/data-deletion-request`: Solicitação de exclusão

## Segurança

O sistema implementa diversas medidas de segurança para proteger dados e funcionalidades.

### Autenticação e Autorização:
- Senhas armazenadas com hash e salt (bcrypt)
- Tokens JWT para autenticação de API
- Controle de acesso baseado em perfis
- Proteção contra ataques de força bruta
- Sessões com timeout configurável

### Proteção de Dados:
- Criptografia de dados sensíveis
- Validação de entrada em todos os formulários
- Proteção contra SQL Injection via ORM
- Proteção contra XSS com escape automático
- CSRF tokens em todos os formulários

### Conformidade LGPD:
- Consentimento explícito para coleta de dados
- Registro de operações em dados pessoais
- Mecanismos de exclusão e anonimização
- Exportação de dados em formato legível
- Políticas de privacidade claras

### Logs e Auditoria:
- Registro de todas as ações sensíveis
- Logs de acesso a dados pessoais
- Logs de autenticação (sucesso/falha)
- Logs de operações administrativas
- Retenção configurável de logs

## Integração com Serviços Externos

O sistema integra-se com diversos serviços externos para expandir suas funcionalidades.

### Google API:
- **Google Calendar**: Sincronização de tarefas com agenda
- **Google OAuth**: Autenticação via conta Google
- **Google Drive**: Backup opcional de arquivos

### Hugging Face:
- Modelos de processamento de linguagem natural
- Classificação automática de documentos
- Extração de entidades e conceitos
- Recomendações baseadas em conteúdo

### Serviços de Email:
- Envio de notificações
- Recuperação de senha
- Confirmação de cadastro
- Alertas de segurança

## Requisitos de Sistema

### Requisitos de Servidor:
- Python 3.10 ou superior
- Banco de dados SQLite (desenvolvimento) ou PostgreSQL 12+ (produção)
- 2GB RAM mínimo (4GB recomendado)
- 10GB de espaço em disco (mínimo)
- Servidor web Nginx ou Apache
- WSGI server (Gunicorn recomendado)

### Dependências Python:
- Flask 2.2+
- SQLAlchemy 1.4+
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Werkzeug
- Jinja2
- PyJWT
- Bcrypt
- Requests
- Pillow
- PyPDF2
- python-docx
- huggingface_hub
- transformers
- google-api-python-client
- google-auth-oauthlib

## Guia de Instalação

### Instalação em Ambiente de Desenvolvimento:

1. Clone o repositório:
   ```
   git clone https://github.com/serraprojetos/consultoria-educacional.git
   cd consultoria-educacional
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

5. Inicialize o banco de dados:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Execute o servidor de desenvolvimento:
   ```
   flask run
   ```

### Instalação em Ambiente de Produção:

1. Clone o repositório:
   ```
   git clone https://github.com/serraprojetos/consultoria-educacional.git
   cd consultoria-educacional
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```
   cp .env.example .env.production
   # Edite o arquivo .env.production com suas configurações de produção
   ```

5. Configure o banco de dados PostgreSQL:
   ```
   # Crie o banco de dados e o usuário no PostgreSQL
   # Atualize a variável DATABASE_URL no arquivo .env.production
   ```

6. Inicialize o banco de dados:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

7. Configure o Nginx:
   ```
   # Exemplo de configuração para Nginx
   server {
       listen 80;
       server_name seu-dominio.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. Configure o Gunicorn:
   ```
   gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
   ```

9. Configure o Supervisor para manter o aplicativo em execução:
   ```
   # Exemplo de configuração para Supervisor
   [program:consultoria-educacional]
   command=/caminho/para/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
   directory=/caminho/para/consultoria-educacional
   user=www-data
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/consultoria-educacional/error.log
   stdout_logfile=/var/log/consultoria-educacional/access.log
   ```

## Manutenção e Backup

### Backups:

O sistema inclui funcionalidades automáticas de backup:

1. **Backups Diários**:
   - Banco de dados completo
   - Arquivos enviados pelos usuários
   - Logs do sistema

2. **Política de Retenção**:
   - Backups diários: mantidos por 7 dias
   - Backups semanais: mantidos por 1 mês
   - Backups mensais: mantidos por 1 ano

3. **Restauração**:
   - Interface administrativa para restauração
   - Opção de restauração parcial (apenas dados específicos)
   - Log detalhado de restaurações

### Atualizações:

Procedimento recomendado para atualizações:

1. Faça backup do sistema atual
2. Clone a nova versão do repositório
3. Atualize as dependências: `pip install -r requirements.txt`
4. Execute as migrações do banco de dados: `flask db upgrade`
5. Reinicie o servidor: `sudo systemctl restart consultoria-educacional`

## Solução de Problemas

### Problemas Comuns:

#### Erro de Conexão com Banco de Dados:
- Verifique se o serviço do banco de dados está em execução
- Confirme as credenciais no arquivo .env
- Verifique permissões do usuário do banco de dados

#### Erro de Upload de Arquivos:
- Verifique as permissões do diretório de uploads
- Confirme o limite de tamanho de arquivo no servidor web
- Verifique o limite de tamanho de arquivo na configuração do Flask

#### Erro de Autenticação OAuth:
- Verifique as credenciais do cliente OAuth
- Confirme se as URLs de redirecionamento estão corretas
- Verifique se as APIs necessárias estão habilitadas

#### Problemas de Desempenho:
- Verifique a utilização de recursos do servidor
- Considere otimizar consultas frequentes
- Verifique logs de erro para identificar gargalos

### Logs:

Os logs do sistema estão disponíveis em:

- Logs de aplicação: `/var/log/consultoria-educacional/`
- Logs do servidor web: `/var/log/nginx/` ou `/var/log/apache2/`
- Logs do banco de dados: Depende da configuração do PostgreSQL

### Contato para Suporte:

Para suporte técnico, entre em contato:

- Email: suporte.tecnico@serraprojetos.com.br
- Telefone: (11) 5555-5555 (horário comercial)
- Sistema de tickets: https://suporte.serraprojetos.com.br
