
#!/bin/bash
# ==============================================================================
# SCRIPT DE INSTALAÇÃO - ARQUITETURA HÍBRIDA (SITE + APP)
# ==============================================================================

# Definição de Caminhos
BASE_DIR="/opt/pmesp-vps"
SERVER_DIR="$BASE_DIR/server"
VENV_DIR="$SERVER_DIR/venv"
SERVICE_NAME="pmesp-web"

echo "🚀 [1/5] INICIANDO INSTALAÇÃO DO SERVIDOR..."

# 1. Atualizar o sistema e instalar dependências básicas
echo "📦 Atualizando pacotes Linux..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git

# 2. Configurar o Ambiente Virtual (Python) dentro da pasta server
echo "🐍 Configurando Python na pasta Server..."
cd $SERVER_DIR

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   -> Ambiente virtual criado."
fi

# Ativa o ambiente e instala as bibliotecas
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "   -> Dependências instaladas."
else
    echo "⚠️  AVISO: requirements.txt não encontrado ainda. O pip falhou."
fi

# 3. Criar arquivo .env de segurança (Se não existir)
if [ ! -f ".env" ]; then
    echo "🔒 Criando arquivo .env padrão..."
    cat <<EOT >> .env
# CONFIGURAÇÕES SECRETAS DA VPS
ROOT_USER=root
ROOT_PASS=Teamo231513.
SSH_PORT=22
JWT_SECRET=ChaveSecretaPadrao123
EOT
    echo "   -> Arquivo .env criado em $SERVER_DIR/.env"
else
    echo "✅ Arquivo .env já existe. Mantendo atual."
fi

# 4. Configurar o serviço Systemd (Para rodar o Site em segundo plano)
echo "⚙️  Configurando serviço Gunicorn..."

sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=PMESP Web Gateway Service
After=network.target

[Service]
User=root
WorkingDirectory=$SERVER_DIR
Environment=\"PATH=$VENV_DIR/bin\"
# Roda o Gunicorn buscando o 'app' dentro do arquivo 'app.py'
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
EOF"

# 5. Reiniciar serviços
echo "🔥 Iniciando o servidor..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Verificação final
STATUS=$(sudo systemctl is-active $SERVICE_NAME)
if [ "$STATUS" == "active" ]; then
    echo "✅ SUCESSO! O servidor Web está rodando."
    echo "📝 IMPORTANTE: Edite a senha em: nano $SERVER_DIR/.env"
else
    echo "❌ O serviço foi criado, mas falhou ao iniciar (Provavelmente falta o arquivo app.py que criaremos a seguir)."
fi
