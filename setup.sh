#!/bin/bash
# INSTALADOR AUTOMÁTICO PMESP MANAGER
# Execute: wget https://raw.githubusercontent.com/ColtSeals/pmesp-vps/main/setup.sh && bash setup.sh

echo -e "\033[1;34m>>> INICIANDO INSTALAÇÃO DO SISTEMA TÁTICO PMESP <<<\033[0m"

# 1. Atualizar sistema e instalar base
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git jq screen nano unzip

# 2. Criar pastas
mkdir -p /root/pmesp_sistema
cd /root/pmesp_sistema

# 3. Baixar arquivos (Simulação do Git Clone ou Wget direto)
# AQUI VOCÊ COLOCA A URL REAL DOS SEUS ARQUIVOS NO GITHUB (RAW)
echo "Baixando arquivos..."
wget -O menu.sh https://raw.githubusercontent.com/ColtSeals/REPO/main/menu.sh
wget -O api.py https://raw.githubusercontent.com/ColtSeals/REPO/main/api/main.py
wget -O requirements.txt https://raw.githubusercontent.com/ColtSeals/REPO/main/api/requirements.txt

# 4. Permissões
chmod +x menu.sh

# 5. Instalar dependências Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 6. Criar Serviço SystemD (Para a API rodar sozinha no fundo)
echo "Criando serviço da API..."
cat <<EOF > /etc/systemd/system/pmesp-api.service
[Unit]
Description=API de Autenticacao PMESP
After=network.target

[Service]
User=root
WorkingDirectory=/root/pmesp_sistema
ExecStart=/root/pmesp_sistema/venv/bin/uvicorn api:app --host 0.0.0.0 --port 54321
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pmesp-api
systemctl start pmesp-api

# 7. Atalho para o menu
echo "alias pmesp='/root/pmesp_sistema/menu.sh'" >> /root/.bashrc
ln -sf /root/pmesp_sistema/menu.sh /usr/bin/pmesp

echo -e "\033[1;32m>>> INSTALAÇÃO CONCLUÍDA! <<<\033[0m"
echo "A API está rodando na porta 54321 (Libere no Firewall)"
echo "Digite 'pmesp' para abrir o menu."
