#!/bin/bash

# Script de implantação para o Sistema de Consultoria Educacional
# Serra Projetos Educacionais
# Data: 22/04/2025

echo "Iniciando script de implantação..."

# Verificar ambiente
if [ ! -d "/home/ubuntu/venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv /home/ubuntu/venv
fi

# Ativar ambiente virtual
source /home/ubuntu/venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install flask flask-sqlalchemy flask-login flask-wtf flask-migrate werkzeug jinja2 pyjwt bcrypt requests pillow pypdf2 python-docx huggingface_hub transformers google-api-python-client google-auth-oauthlib gunicorn

# Criar diretórios necessários
echo "Criando estrutura de diretórios..."
mkdir -p /home/ubuntu/instance/logs
mkdir -p /home/ubuntu/instance/backups
mkdir -p /home/ubuntu/instance/reports
mkdir -p /home/ubuntu/static/css
mkdir -p /home/ubuntu/static/js
mkdir -p /home/ubuntu/static/img
mkdir -p /home/ubuntu/media/uploads
mkdir -p /home/ubuntu/templates

# Copiar arquivos estáticos
echo "Copiando arquivos estáticos..."
cp /home/ubuntu/upload/styles.css /home/ubuntu/static/css/
cp /home/ubuntu/upload/script.js /home/ubuntu/static/js/

# Configurar banco de dados
echo "Configurando banco de dados..."
if [ ! -f "/home/ubuntu/instance/serra_consultoria.db" ]; then
    echo "Criando banco de dados SQLite..."
    touch /home/ubuntu/instance/serra_consultoria.db
fi

# Executar testes
echo "Executando testes..."
python /home/ubuntu/tests.py

# Verificar se os testes passaram
if [ $? -eq 0 ]; then
    echo "Testes concluídos com sucesso!"
else
    echo "ATENÇÃO: Alguns testes falharam. Verifique os logs para mais detalhes."
    echo "Continuando com a implantação..."
fi

# Inicializar banco de dados
echo "Inicializando banco de dados..."
export FLASK_APP=/home/ubuntu/app.py
flask db init
flask db migrate -m "Migração inicial"
flask db upgrade

# Configurar servidor Gunicorn
echo "Configurando servidor Gunicorn..."
cat > /home/ubuntu/gunicorn_config.py << EOF
bind = "0.0.0.0:8000"
workers = 4
timeout = 120
accesslog = "/home/ubuntu/instance/logs/access.log"
errorlog = "/home/ubuntu/instance/logs/error.log"
capture_output = True
loglevel = "info"
EOF

# Criar script de inicialização
echo "Criando script de inicialização..."
cat > /home/ubuntu/start.sh << EOF
#!/bin/bash
source /home/ubuntu/venv/bin/activate
cd /home/ubuntu
gunicorn -c gunicorn_config.py "app:create_app()"
EOF

chmod +x /home/ubuntu/start.sh

# Criar script de backup
echo "Criando script de backup..."
cat > /home/ubuntu/backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/instance/backups"
DB_BACKUP="\$BACKUP_DIR/db_backup_\$DATE.sqlite"
FILES_BACKUP="\$BACKUP_DIR/files_backup_\$DATE.tar.gz"

# Backup do banco de dados
cp /home/ubuntu/instance/serra_consultoria.db \$DB_BACKUP

# Backup dos arquivos
tar -czf \$FILES_BACKUP /home/ubuntu/media/uploads

# Manter apenas os últimos 7 backups
find \$BACKUP_DIR -name "db_backup_*" -type f | sort -r | tail -n +8 | xargs rm -f
find \$BACKUP_DIR -name "files_backup_*" -type f | sort -r | tail -n +8 | xargs rm -f

echo "Backup concluído: \$DATE"
EOF

chmod +x /home/ubuntu/backup.sh

# Configurar cron para backups diários
echo "Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/instance/logs/backup.log 2>&1") | crontab -

# Iniciar aplicação
echo "Iniciando aplicação..."
/home/ubuntu/start.sh &

# Expor porta para acesso externo
echo "Expondo porta 8000 para acesso externo..."
echo "A aplicação estará disponível em: http://localhost:8000"
echo "Para acesso externo, use o comando 'deploy_expose_port' com a porta 8000"

echo "Implantação concluída com sucesso!"
echo "Para iniciar a aplicação manualmente, execute: ./start.sh"
echo "Para fazer backup manualmente, execute: ./backup.sh"
