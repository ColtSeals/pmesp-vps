#!/bin/bash
# Script simples de setup da API PMESP na VPS

set -e

echo "[+] Detectando raiz do projeto..."
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[+] Instalando pacotes básicos do sistema..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip

echo "[+] Criando ambiente virtual..."
python3 -m venv venv

echo "[+] Ativando ambiente virtual e instalando dependências..."
source venv/bin/activate
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" SQLAlchemy "pydantic[email]"

echo ""
echo "[OK] Ambiente pronto!"
echo "Para iniciar a API, rode:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
