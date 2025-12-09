import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

# --- CONFIGURAÇÃO ---
# A chave secreta deve ser carregada de forma segura do config_base.py 
# ou de variáveis de ambiente.
# JWT_SECRET_KEY é usada para assinar (proteger) o token.
# JWT_ALGORITHM é o algoritmo de criptografia.

# Usaremos esta chave secreta como placeholder; você deve mudá-la no ambiente de produção.
JWT_SECRET_KEY = "sua_chave_secreta_muito_forte_aqui_12345" 
JWT_ALGORITHM = "HS256"
# Token expira em 3 horas
ACCESS_TOKEN_EXPIRE_MINUTES = 180 

# =================================================================
# 1. GERAÇÃO DE TOKEN
# =================================================================

def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Gera um novo Token JWT contendo o ID do usuário e seu nível de acesso (role).
    """
    to_encode = {
        "sub": user_id,
        "role": role,  # 'user' ou 'admin'
        "iat": datetime.now(timezone.utc).timestamp(), # Timestamp de emissão
    }
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire.timestamp()})
    
    # Assina (protege) o token com a chave secreta
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# =================================================================
# 2. VALIDAÇÃO E DECODIFICAÇÃO
# =================================================================

def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decodifica o Token JWT. Retorna o payload se válido, ou None se inválido/expirado.
    """
    try:
        # Decodifica e verifica a assinatura e a validade (expiração)
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Erro de token expirado
        print("ERRO JWT: Token expirado.")
        return None
    except jwt.InvalidTokenError:
        # Erro de token inválido (assinatura incorreta, etc.)
        print("ERRO JWT: Token inválido.")
        return None

# =================================================================
# 3. DECORATOR DE AUTORIZAÇÃO (Para uso no app_api.py)
# =================================================================

def requires_role(required_role: str):
    """
    Decorator para proteger rotas da API, garantindo que apenas usuários com a 'role'
    necessária possam acessar.
    """
    from functools import wraps
    from flask import request, jsonify
    
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 1. Tenta obter o Token do cabeçalho 'Authorization'
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"mensagem": "Token de acesso não fornecido."}), 401

            token = auth_header.split(" ")[1]
            
            # 2. Decodifica o Token
            payload = decode_access_token(token)
            if payload is None:
                return jsonify({"mensagem": "Token inválido ou expirado."}), 401
            
            user_role = payload.get("role")
            
            # 3. Verifica o Nível de Acesso (Role)
            if user_role != required_role and user_role != 'admin':
                # Nota: 'admin' sempre pode acessar rotas 'user'
                if required_role == 'user' and user_role == 'admin':
                    pass # Admin tem acesso
                else:
                    return jsonify({"mensagem": "Acesso negado. Privilégios insuficientes."}), 403

            # Adiciona os dados do usuário na requisição para a função de rota usar
            request.user_data = payload
            return f(*args, **kwargs)
        return decorated
    return wrapper

# Exemplo de uso no app_api.py:
# @app.route('/admin/dashboard')
# @requires_role('admin')
# def admin_dashboard():
#    ...

