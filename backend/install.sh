#!/bin/bash
# Instalação Profissional PMESP Backend
echo ">>> Atualizando sistema..."
apt-get update && apt-get install -y python3-pip python3-venv sqlite3 libsqlite3-dev

# Cria diretório da aplicação
mkdir -p /opt/pmesp-api
cd /opt/pmesp-api

# Cria ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instala dependências da API
pip install fastapi uvicorn sqlalchemy pydantic passlib[bcrypt] python-multipart psutil pyjwt

echo ">>> Criando serviço do sistema..."
cat <<EOF > /etc/systemd/system/pmesp-api.service
[Unit]
Description=PMESP API Backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/pmesp-api
ExecStart=/opt/pmesp-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pmesp-api
echo ">>> Ambiente pronto. Agora suba os arquivos Python (main.py, database.py) para /opt/pmesp-api/"
