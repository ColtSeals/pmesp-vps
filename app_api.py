from flask import Flask, request, jsonify
import paramiko
import json
import os
from datetime import datetime

# Importações dos módulos locais
import config_base
import auth_jwt
from admin_core import AdminCore

app = Flask(__name__)

# Inicializa o núcleo de administração
core = AdminCore()

# =================================================================
# 1. API DE CONFIGURAÇÃO (Dinâmica: Desktop vs Android)
# =================================================================
@app.route('/api/v1/config/ui', methods=['GET'])
def get_ui_config():
    """
    Retorna o JSON de layout baseado na plataforma solicitada.
    Ex: /api/v1/config/ui?platform=android
    """
    platform = request.args.get('platform', 'desktop').lower()
    
    filename = "config_android.json" if platform == "android" else "config_desktop.json"
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"sucesso": True, "config": data})
    except FileNotFoundError:
        # Fallback se o arquivo não existir
        return jsonify({
            "sucesso": True, 
            "config": {
                "PRIMARY_COLOR": "#3b82f6",
                "BG_COLOR": "#09090b",
                "TITULO": "SISTEMA INTEGRADO (MODO DE SEGURANÇA)"
            }
        })

# =================================================================
# 2. AUTENTICAÇÃO E REGISTRO (Login, HWID, Cadastro)
# =================================================================

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Cria novo usuário no Linux e no JSON."""
    data = request.get_json()
    usuario = data.get('usuario')
    senha = data.get('senha')
    email = data.get('email', '')
    matricula = data.get('matricula', '')

    if not usuario or not senha:
        return jsonify({"sucesso": False, "mensagem": "Usuário e senha obrigatórios."}), 400

    # Chama o admin_core para criar no sistema
    sucesso, msg = core.create_linux_user(usuario, senha, email, matricula)
    
    if sucesso:
        return jsonify({"sucesso": True, "mensagem": msg})
    else:
        return jsonify({"sucesso": False, "mensagem": msg}), 400

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """
    Processo completo de Login:
    1. Valida senha SSH (Paramiko)
    2. Verifica JSON (Validade, Limite, Role)
    3. Verifica/Registra HWID
    4. Retorna Token JWT + Dados do Usuário
    """
    data = request.get_json()
    usuario = data.get('usuario')
    senha = data.get('senha')
    client_hwid = data.get('hwid')

    # --- PASSO 1: Autenticação SSH (Senha correta?) ---
    try:
        ssh_check = paramiko.SSHClient()
        ssh_check.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Tenta conectar no localhost ou IP externo para validar senha
        # Se SSH_PORT for diferente de 22, ajuste no config_base.py
        ssh_check.connect(hostname="127.0.0.1", port=config_base.SSH_PORT, username=usuario, password=senha, timeout=5)
        ssh_check.close()
    except Exception:
        return jsonify({"sucesso": False, "tipo_erro": "SENHA", "mensagem": "Credenciais inválidas."}), 401

    # --- PASSO 2: Dados do Usuário (JSON) ---
    user_data = core.get_user_data(usuario)
    if not user_data:
        # Se logou no SSH mas não está no JSON, nega acesso
        return jsonify({"sucesso": False, "mensagem": "Usuário sem registro no banco de dados."}), 403

    # Validade (Dias)
    try:
        dias = int(user_data.get('dias', 0))
        if dias <= 0:
            return jsonify({"sucesso": False, "tipo_erro": "VENCIDO", "mensagem": "Licença expirada."}), 403
    except: pass

    # Limite de Sessões
    limite = int(user_data.get('limite', 1))
    ativas = core.check_active_sessions(usuario)
    if ativas >= limite:
        return jsonify({"sucesso": False, "tipo_erro": "LIMITE", "mensagem": f"Limite excedido ({ativas}/{limite})."}), 403

    # --- PASSO 3: HWID ---
    hwid_ok, hwid_msg = core.validate_hwid(usuario, client_hwid)
    if not hwid_ok:
        return jsonify({"sucesso": False, "tipo_erro": "HWID", "mensagem": hwid_msg}), 403

    # --- PASSO 4: Gerar Token JWT ---
    role = user_data.get('role', 'user') 
    token = auth_jwt.create_access_token(user_id=usuario, role=role)

    return jsonify({
        "sucesso": True,
        "token": token,
        "role": role,
        "dados_usuario": {
            "matricula": user_data.get('matricula'),
            "email": user_data.get('email'),
            "dias": dias,
            "limite": limite,
            "ssh_user": usuario,
            "ssh_pass": senha, 
            "ssh_host": config_base.API_HOST,
            "ssh_port": config_base.SSH_PORT
        }
    })

# =================================================================
# 3. ROTAS DO USUÁRIO (Chamados, Senha)
# =================================================================

@app.route('/api/v1/user/change_password', methods=['POST'])
@auth_jwt.requires_role('user') 
def change_pass():
    data = request.get_json()
    usuario_atual = request.user_data['sub'] 
    nova_senha = data.get('nova_senha')

    if not nova_senha:
        return jsonify({"sucesso": False, "mensagem": "Senha vazia."}), 400

    if core.change_password(usuario_atual, nova_senha):
        return jsonify({"sucesso": True, "mensagem": "Senha alterada com sucesso!"})
    else:
        return jsonify({"sucesso": False, "mensagem": "Erro ao alterar senha."}), 500

@app.route('/api/v1/tickets/new', methods=['POST'])
@auth_jwt.requires_role('user')
def new_ticket():
    data = request.get_json()
    usuario = request.user_data['sub']
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    categoria = data.get('categoria')

    log_entry = f"[{datetime.now()}] USER: {usuario} | CAT: {categoria} | TITULO: {titulo} | DESC: {descricao}\n"
    with open("tickets.log", "a") as f:
        f.write(log_entry)

    return jsonify({"sucesso": True, "mensagem": "Chamado registrado #Ticket-LOG"})

# =================================================================
# 4. ROTAS DE ADMINISTRAÇÃO (Só Admin acessa)
# =================================================================

@app.route('/api/v1/admin/users', methods=['GET'])
@auth_jwt.requires_role('admin')
def list_users():
    users = core.get_all_users()
    for u in users:
        u.pop('senha', None) # Remove senha visualmente
    return jsonify({"sucesso": True, "users": users})

@app.route('/api/v1/admin/user/update', methods=['POST'])
@auth_jwt.requires_role('admin')
def update_user_admin():
    data = request.get_json()
    target_user = data.get('usuario_alvo')
    novos_dados = data.get('dados')

    if not target_user or not novos_dados:
        return jsonify({"sucesso": False, "mensagem": "Dados incompletos."}), 400

    if core.update_user_json(target_user, novos_dados):
        return jsonify({"sucesso": True, "mensagem": f"Usuário {target_user} atualizado."})
    else:
        return jsonify({"sucesso": False, "mensagem": "Erro ao atualizar usuário."}), 500

@app.route('/api/v1/admin/user/reset_hwid', methods=['POST'])
@auth_jwt.requires_role('admin')
def reset_hwid():
    data = request.get_json()
    target_user = data.get('usuario_alvo')
    
    if core.update_user_json(target_user, {"hwid": "PENDENTE"}):
        return jsonify({"sucesso": True, "mensagem": "HWID resetado para PENDENTE."})
    else:
        return jsonify({"sucesso": False, "mensagem": "Erro ao resetar HWID."}), 500

if __name__ == '__main__':
    port = config_base.API_PORT
    app.run(host='0.0.0.0', port=port)
                            
