import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (segurança)
# O arquivo .env deve ser criado manualmente na VPS e NUNCA deve ser commitado no GitHub.
load_dotenv() 

# =================================================================
# 1. CONFIGURAÇÕES DA VPS / SERVIDOR
# =================================================================

# IP e Porta da VPS que hospeda o servidor API (Para comunicação cliente-servidor)
# O cliente (Flet) fará requisições para este endereço.
API_HOST = os.getenv("API_HOST", "127.0.0.1") # Ex: "sua_vps.com" ou IP
API_PORT = int(os.getenv("API_PORT", 5000))

# Chave Secreta do JWT para assinar os tokens (USO OBRIGATÓRIO EM PRODUÇÃO)
# Esta chave deve ser longa e complexa. Carregada de forma segura.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SUA_CHAVE_SECRETA_PADRAO_MUITO_LONGA_E_COMPLEXA_987654321")

# O algoritmo de criptografia usado para o JWT
JWT_ALGORITHM = "HS256"

# Tempo de expiração do token (em minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 180 

# =================================================================
# 2. CREDENCIAIS DE ALTO PRIVILÉGIO (ROOT)
# =================================================================

# Credenciais de acesso SSH ROOT da VPS (para uso APENAS no admin_core.py)
# ESTAS VARIÁVEIS NUNCA DEVEM SER EXPOSTAS DIRETAMENTE NO GITHUB.
ROOT_USER = os.getenv("ROOT_USER", "root")
ROOT_PASS = os.getenv("ROOT_PASS", "SENHA_ROOT_MUITO_FORTE_MUDE_NO_DOT_ENV")
# Porta SSH da VPS
SSH_PORT = int(os.getenv("SSH_PORT", 22))

# IP do servidor onde o túnel SOCKS será criado (pode ser o mesmo IP da VPS)
# O cliente Flet se conectará a esta porta SOCKS após o login.
SOCKS_BIND_IP = "0.0.0.0" 
SOCKS_PORT = 1080 

# =================================================================
# 3. CONFIGURAÇÕES INTERNAS
# =================================================================

# Caminho para o arquivo JSON de usuários que será gerenciado pelo admin_core.py
USER_JSON_PATH = "users_data.json"

