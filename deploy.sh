#!/bin/bash

# ==============================================================================
# SCRIPT DE INSTALAÇÃO AUTOMÁTICA - PMESP VPS
# Repositório: https://github.com/ColtSeals/pmesp-vps.git
# ==============================================================================

APP_DIR="/opt/pmesp-vps"
REPO_URL="https://github.com/ColtSeals/pmesp-vps.git"
SERVICE_NAME="pmesp-api"

echo "🚀 INICIANDO INSTALAÇÃO DO SERVIDOR..."

# 1. ATUALIZAR SISTEMA E INSTALAR DEPENDÊNCIAS
echo "📦 Atualizando pacotes e instalando Python/Git..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git

# 2. CLONAR OU ATUALIZAR O REPOSITÓRIO
if [ -d "$APP_DIR" ]; then
    echo "🔄 Diretório encontrado. Atualizando repositório..."
    cd $APP_DIR
    git pull
else
    echo "📥 Clonando repositório pela primeira vez..."
    sudo git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# 3. CONFIGURAR AMBIENTE VIRTUAL (VENV)
echo "🐍 Configurando ambiente Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
# Instala as bibliotecas do requirements.txt
pip install -r requirements.txt

# 4. CRIAR ARQUIVO .ENV (SE NÃO EXISTIR)
# Isso é importante para você colocar suas senhas depois sem subir no GitHub
if [ ! -f ".env" ]; then
    echo "🔒 Criando arquivo .env padrão (EDITE-O DEPOIS COM SUAS SENHAS REAL!)..."
    cat <<EOT >> .env
# CONFIGURAÇÕES DE SEGURANÇA (NÃO COMPARTILHE)
API_HOST=0.0.0.0
API_PORT=5000
JWT_SECRET_KEY=MUDE_ISSO_PARA_UMA_CHAVE_SECRETA_MUITO_LONGA_AGORA
ROOT_USER=root
ROOT_PASS=SuaSenhaDeRootRealAqui
SSH_PORT=22
EOT
else
    echo "✅ Arquivo .env já existe. Mantendo configurações atuais."
fi

# 5. CONFIGURAR O SERVIÇO SYSTEMD (PARA RODAR EM SEGUNDO PLANO)
echo "⚙️ Configurando serviço Systemd..."

# Cria o arquivo de serviço
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Gunicorn instance to serve PMESP API
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
# Comando para iniciar o servidor com Gunicorn (3 workers)
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app_api:app

[Install]
WantedBy=multi-user.target
EOF"

# 6. INICIAR O SERVIÇO
echo "🔥 Iniciando a API..."
sudo systemctl daemon-reload
sudo systemctl start $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Verifica status
STATUS=$(sudo systemctl is-active $SERVICE_NAME)
if [ "$STATUS" == "active" ]; then
    echo "✅ SUCESSO! A API está rodando."
    echo "⚠️ IMPORTANTE: Edite o arquivo $APP_DIR/.env para colocar a SENHA DO ROOT correta!"
    echo "📝 Comando para editar: nano $APP_DIR/.env"
    echo "🔄 Depois de editar, reinicie com: sudo systemctl restart $SERVICE_NAME"
else
    echo "❌ Ocorreu um erro ao iniciar o serviço. Verifique os logs com: journalctl -u $SERVICE_NAME"
fi

