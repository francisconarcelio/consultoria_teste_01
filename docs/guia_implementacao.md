# Guia de Implementação - Sistema de Consultoria Educacional

## Sumário

1. [Introdução](#introdução)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração do Ambiente](#configuração-do-ambiente)
4. [Implementação Passo a Passo](#implementação-passo-a-passo)
5. [Personalização](#personalização)
6. [Testes](#testes)
7. [Implantação](#implantação)
8. [Pós-implantação](#pós-implantação)
9. [Checklist de Implementação](#checklist-de-implementação)

## Introdução

Este guia fornece instruções detalhadas para implementação do Sistema de Consultoria Educacional da Serra Projetos Educacionais em um ambiente de produção. O documento é destinado a administradores de sistemas e desenvolvedores responsáveis pela configuração e personalização do sistema.

## Pré-requisitos

Antes de iniciar a implementação, certifique-se de que os seguintes pré-requisitos estão atendidos:

### Hardware:
- Servidor com pelo menos 4GB de RAM
- Mínimo de 20GB de espaço em disco (recomendado 50GB para crescimento)
- Processador com 2 ou mais núcleos

### Software:
- Sistema operacional Linux (Ubuntu 20.04 LTS ou superior recomendado)
- Python 3.10 ou superior
- PostgreSQL 12 ou superior
- Nginx ou Apache
- Git

### Contas e Credenciais:
- Conta de desenvolvedor Google (para APIs do Google)
- Conta Hugging Face (para acesso aos modelos de IA)
- Domínio registrado e configurado (para ambiente de produção)
- Certificado SSL (recomendado Let's Encrypt)

## Configuração do Ambiente

### 1. Preparação do Servidor

```bash
# Atualizar o sistema
sudo apt update
sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

# Instalar ferramentas de desenvolvimento
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 2. Configuração do PostgreSQL

```bash
# Criar usuário e banco de dados
sudo -u postgres psql -c "CREATE USER serraapp WITH PASSWORD 'senha_segura';"
sudo -u postgres psql -c "CREATE DATABASE serra_consultoria;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE serra_consultoria TO serraapp;"
sudo -u postgres psql -c "ALTER USER serraapp WITH SUPERUSER;"
```

### 3. Configuração do Nginx

Crie um arquivo de configuração para o site:

```bash
sudo nano /etc/nginx/sites-available/serra-consultoria
```

Adicione o seguinte conteúdo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /caminho/para/serra-consultoria/static;
    }

    location /media {
        alias /caminho/para/serra-consultoria/media;
    }

    client_max_body_size 20M;
}
```

Ative a configuração:

```bash
sudo ln -s /etc/nginx/sites-available/serra-consultoria /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configuração do SSL (Opcional, mas recomendado)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com.br

# Configurar renovação automática
sudo systemctl status certbot.timer
```

## Implementação Passo a Passo

### 1. Clonar o Repositório

```bash
# Criar diretório para a aplicação
sudo mkdir -p /opt/serra-consultoria
sudo chown $USER:$USER /opt/serra-consultoria

# Clonar o repositório
git clone https://github.com/serraprojetos/consultoria-educacional.git /opt/serra-consultoria
cd /opt/serra-consultoria
```

### 2. Configurar o Ambiente Virtual

```bash
# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
nano /opt/serra-consultoria/.env
```

Adicione as seguintes variáveis:

```
# Configurações Gerais
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=chave_secreta_muito_segura_e_aleatoria

# Banco de Dados
DATABASE_URL=postgresql://serraapp:senha_segura@localhost/serra_consultoria

# Email
MAIL_SERVER=smtp.seu-provedor.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@seu-provedor.com
MAIL_PASSWORD=sua_senha_de_email
MAIL_DEFAULT_SENDER=seu-email@seu-provedor.com

# Google API
GOOGLE_CLIENT_ID=seu_client_id_do_google
GOOGLE_CLIENT_SECRET=seu_client_secret_do_google
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration

# Hugging Face
HUGGINGFACE_API_KEY=sua_api_key_do_huggingface

# Configurações de Upload
UPLOAD_FOLDER=/opt/serra-consultoria/media/uploads
MAX_CONTENT_LENGTH=10485760  # 10MB em bytes

# Configurações de Segurança
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
REMEMBER_COOKIE_HTTPONLY=True
```

### 4. Inicializar o Banco de Dados

```bash
# Ativar o ambiente virtual se não estiver ativado
source /opt/serra-consultoria/venv/bin/activate

# Inicializar o banco de dados
cd /opt/serra-consultoria
flask db init
flask db migrate -m "Inicialização do banco de dados"
flask db upgrade
```

### 5. Criar Diretórios Necessários

```bash
# Criar diretórios para uploads e logs
mkdir -p /opt/serra-consultoria/media/uploads
mkdir -p /opt/serra-consultoria/logs
mkdir -p /opt/serra-consultoria/instance/backups
```

### 6. Configurar o Supervisor

Instale o Supervisor para gerenciar o processo da aplicação:

```bash
sudo apt install -y supervisor
```

Crie um arquivo de configuração:

```bash
sudo nano /etc/supervisor/conf.d/serra-consultoria.conf
```

Adicione o seguinte conteúdo:

```ini
[program:serra-consultoria]
directory=/opt/serra-consultoria
command=/opt/serra-consultoria/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/opt/serra-consultoria/logs/gunicorn.err.log
stdout_logfile=/opt/serra-consultoria/logs/gunicorn.out.log
environment=
    FLASK_APP="app.py",
    FLASK_ENV="production",
    PATH="/opt/serra-consultoria/venv/bin"
```

Atualize as permissões e inicie o serviço:

```bash
sudo chown -R www-data:www-data /opt/serra-consultoria
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start serra-consultoria
```

## Personalização

### 1. Personalização Visual

Para personalizar a aparência do sistema:

1. Edite os arquivos CSS em `/opt/serra-consultoria/static/css/`
2. Substitua o logo em `/opt/serra-consultoria/static/img/logo.png`
3. Atualize as cores e fontes no arquivo `/opt/serra-consultoria/static/css/styles.css`

### 2. Configuração de Email

Personalize os templates de email em `/opt/serra-consultoria/templates/email/`:

1. `welcome_email.html`: Email de boas-vindas
2. `password_reset.html`: Email de recuperação de senha
3. `notification.html`: Template para notificações

### 3. Configuração de Integrações

#### Google Calendar:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a API do Google Calendar
4. Configure as credenciais OAuth
5. Adicione as credenciais ao arquivo `.env`

#### Hugging Face:

1. Crie uma conta no [Hugging Face](https://huggingface.co/)
2. Gere uma API key
3. Adicione a API key ao arquivo `.env`
4. Configure os modelos desejados no arquivo `huggingface_integration.py`

## Testes

Antes de disponibilizar o sistema para os usuários finais, realize os seguintes testes:

### 1. Teste de Funcionalidades

```bash
# Ativar o ambiente virtual
source /opt/serra-consultoria/venv/bin/activate

# Executar testes automatizados
cd /opt/serra-consultoria
python -m pytest
```

### 2. Teste de Segurança

Verifique a segurança do sistema:

1. Teste de autenticação e autorização
2. Validação de entradas
3. Proteção contra CSRF
4. Configurações de cookies seguros
5. Proteção contra XSS

### 3. Teste de Desempenho

Avalie o desempenho do sistema:

1. Tempo de resposta das páginas
2. Capacidade de upload de arquivos
3. Desempenho do banco de dados
4. Uso de memória e CPU

## Implantação

### 1. Verificação Final

Antes da implantação final, verifique:

- Todas as configurações estão corretas
- O banco de dados está inicializado
- Os serviços estão em execução
- Os diretórios têm as permissões corretas
- O SSL está configurado corretamente

### 2. Backup Inicial

Crie um backup inicial do banco de dados:

```bash
pg_dump -U serraapp serra_consultoria > /opt/serra-consultoria/instance/backups/initial_backup.sql
```

### 3. Lançamento

1. Verifique se o sistema está acessível pelo domínio configurado
2. Teste o login e as funcionalidades principais
3. Monitore os logs para identificar possíveis problemas

## Pós-implantação

### 1. Monitoramento

Configure o monitoramento do sistema:

1. Verifique regularmente os logs em `/opt/serra-consultoria/logs/`
2. Configure alertas para erros críticos
3. Monitore o uso de recursos do servidor

### 2. Backups Regulares

Configure backups automáticos:

```bash
# Criar script de backup
nano /opt/serra-consultoria/scripts/backup.sh
```

Adicione o seguinte conteúdo:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/serra-consultoria/instance/backups"
DB_BACKUP="$BACKUP_DIR/db_backup_$DATE.sql"
FILES_BACKUP="$BACKUP_DIR/files_backup_$DATE.tar.gz"

# Backup do banco de dados
pg_dump -U serraapp serra_consultoria > $DB_BACKUP

# Backup dos arquivos
tar -czf $FILES_BACKUP /opt/serra-consultoria/media/uploads

# Manter apenas os últimos 7 backups diários
find $BACKUP_DIR -name "db_backup_*" -type f -mtime +7 -delete
find $BACKUP_DIR -name "files_backup_*" -type f -mtime +7 -delete
```

Configure permissões e cron:

```bash
chmod +x /opt/serra-consultoria/scripts/backup.sh

# Adicionar ao crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/serra-consultoria/scripts/backup.sh") | crontab -
```

### 3. Atualizações

Para atualizar o sistema:

```bash
# Parar o serviço
sudo supervisorctl stop serra-consultoria

# Fazer backup
pg_dump -U serraapp serra_consultoria > /opt/serra-consultoria/instance/backups/pre_update_backup.sql

# Atualizar o código
cd /opt/serra-consultoria
git pull

# Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# Aplicar migrações do banco de dados
flask db upgrade

# Reiniciar o serviço
sudo supervisorctl start serra-consultoria
```

## Checklist de Implementação

Use esta checklist para garantir que todos os aspectos da implementação foram abordados:

- [ ] Servidor configurado com todos os requisitos
- [ ] Banco de dados PostgreSQL instalado e configurado
- [ ] Nginx configurado com SSL
- [ ] Repositório clonado e ambiente virtual configurado
- [ ] Variáveis de ambiente definidas
- [ ] Banco de dados inicializado
- [ ] Diretórios necessários criados com permissões corretas
- [ ] Supervisor configurado e serviço em execução
- [ ] Personalizações visuais aplicadas
- [ ] Integrações configuradas (Google, Hugging Face)
- [ ] Testes de funcionalidades realizados
- [ ] Testes de segurança realizados
- [ ] Testes de desempenho realizados
- [ ] Backup inicial criado
- [ ] Sistema acessível pelo domínio configurado
- [ ] Monitoramento configurado
- [ ] Backups automáticos configurados
- [ ] Procedimento de atualização documentado e testado

Seguindo este guia de implementação, você terá um sistema de consultoria educacional completo, seguro e pronto para uso em ambiente de produção.
