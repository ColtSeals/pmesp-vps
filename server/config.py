
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (que fica na VPS)
load_dotenv()

# Definições de Segurança
# Se não encontrar no .env, usa os valores padrão (segundo parâmetro)
ROOT_USER = os.getenv("ROOT_USER", "root")
ROOT_PASS = os.getenv("ROOT_PASS", "senha_indefinida")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
JWT_SECRET = os.getenv("JWT_SECRET", "chave_secreta_padrao")

# IP da API (Geralmente 0.0.0.0 na VPS)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
