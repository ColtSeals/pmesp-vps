
from flask import Flask, render_template, request, jsonify
import config
from admin_core import AdminCore

# Inicializa o Flask e o Núcleo de Admin
app = Flask(__name__)
core = AdminCore()

# ==============================================================================
# ROTA 1: ENTREGAR O SITE (FRONT-END)
# ==============================================================================
@app.route('/')
def home():
    """
    Entrega o arquivo HTML que está na pasta templates.
    É aqui que o App vai carregar a interface visual.
    """
    return render_template('index.html')

# ==============================================================================
# ROTA 2: API DE LOGIN (BACK-END)
# ==============================================================================
@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Recebe usuario e senha do JavaScript.
    Valida no Linux via SSH Local.
    Retorna os dados para o App ligar o túnel.
    """
    data = request.get_json()
    usuario = data.get('usuario')
    senha = data.get('senha')

    if not usuario or not senha:
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos."}), 400

    # 1. Valida se a senha está correta no Linux da VPS
    if core.validar_login_linux(usuario, senha):
        
        # 2. Se deu certo, retorna os dados para o Python do Celular criar o túnel
        return jsonify({
            "sucesso": True,
            "mensagem": "Login autorizado.",
            "dados_conexao": {
                # O App vai conectar neste IP (IP da VPS)
                "ssh_host": config.API_HOST if config.API_HOST != "0.0.0.0" else request.host.split(':')[0],
                "ssh_port": config.SSH_PORT,
                "ssh_user": usuario,
                "ssh_pass": senha # Envia a senha para o Paramiko do celular usar
            }
        })
    else:
        return jsonify({"sucesso": False, "mensagem": "Usuário ou Senha incorretos."}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
