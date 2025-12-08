#!/bin/bash
# INSTALADOR AUTOMÁTICO - PMESP MANAGER
# Repositório: ColtSeals/pmesp-vps

# --- CONFIGURAÇÕES ---
DIR_INSTALL="/root/pmesp_sistema"

# CORREÇÃO: URL EXATA DO SEU REPOSITÓRIO
REPO_RAW="https://raw.githubusercontent.com/ColtSeals/pmesp-vps/refs/heads/main"
# Nota: Se o link acima falhar, tente: "https://raw.githubusercontent.com/ColtSeals/pmesp-vps/main"

echo -e "\033[1;34m>>> INICIANDO INSTALAÇÃO DO PMESP MANAGER (CORRIGIDO) <<<\033[0m"

# 1. Preparar Sistema
echo "Atualizando pacotes..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git jq screen nano unzip curl wget

# 2. Limpar Instalação Anterior (Importante pois a anterior falhou)
rm -rf "$DIR_INSTALL"
mkdir -p "$DIR_INSTALL"
mkdir -p "$DIR_INSTALL/api"

# 3. Baixar Arquivos do GitHub (URL Corrigida)
echo "Baixando arquivos de: $REPO_RAW"

wget -q -O "$DIR_INSTALL/menu.sh" "$REPO_RAW/menu.sh"
wget -q -O "$DIR_INSTALL/api/main.py" "$REPO_RAW/api/main.py"
wget -q -O "$DIR_INSTALL/api/requirements.txt" "$REPO_RAW/api/requirements.txt"

# Verificação de Segurança
if [ ! -s "$DIR_INSTALL/menu.sh" ]; then
    echo -e "\033[1;31mERRO CRÍTICO: O download falhou novamente.\033[0m"
    echo "Verifique se os arquivos 'menu.sh' e a pasta 'api' existem no GitHub."
    echo "URL tentada: $REPO_RAW/menu.sh"
    exit 1
fi

# 4. Configurar Permissões e Atalho
chmod +x "$DIR_INSTALL/menu.sh"
ln -sf "$DIR_INSTALL/menu.sh" /usr/bin/menu

# 5. Configurar Python da API
echo "Instalando dependências da API..."
cd "$DIR_INSTALL/api" || exit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
deactivate

# 6. Serviço SystemD
cat <<EOF > /etc/systemd/system/pmesp-api.service
[Unit]
Description=API PMESP Backend
After=network.target

[Service]
User=root
WorkingDirectory=$DIR_INSTALL/api
ExecStart=$DIR_INSTALL/api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 54321
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pmesp-api
systemctl restart pmesp-api

echo -e "\033[1;32m>>> INSTALAÇÃO CONCLUÍDA! <<<\033[0m"
echo "Agora deve funcionar."
echo -e "Digite: \033[1;33mmenu\033[0m"
