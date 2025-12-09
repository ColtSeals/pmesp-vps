# pmesp-vps/server/app.py
from flask import Flask, request, jsonify
import config
from admin_core import AdminCore

app = Flask(__name__)
core = AdminCore()

# --- AQUI VOCÊ CONTROLA O DESIGN DO APP ---
LAYOUT_APP = {
    "config_janela": {
        "titulo": "SISTEMA PMESP",
        "cor_fundo": "#09090b",  # Preto Fundo
        "tema_escuro": True
    },
    "tela_login": [
        {"tipo": "espaco", "tamanho": 50},
        {"tipo": "icone", "nome": "security", "tamanho": 80, "cor": "#2563eb"}, # Azul
        {"tipo": "texto", "valor": "GATEWAY SEGURO", "tamanho": 20, "cor": "#ffffff", "peso": "bold"},
        {"tipo": "espaco", "tamanho": 30},
        {"tipo": "input", "id": "usuario", "label": "RE / Usuário", "icone": "person"},
        {"tipo": "input", "id": "senha", "label": "Senha de Rede", "icone": "lock", "senha": True},
        {"tipo": "espaco", "tamanho": 20},
        {"tipo": "botao", "texto": "CONECTAR TÚNEL SSH", "acao": "login", "cor": "#2563eb", "largura": 300}
    ],
    "tela_home": [
        {"tipo": "texto", "valor": "SISTEMAS INTEGRADOS", "tamanho": 18, "cor": "#888888", "peso": "bold"},
        {"tipo": "espaco", "tamanho": 20},
        {"tipo": "grid_botoes", "itens": [
            {"titulo": "MURALHA", "icone": "camera_alt", "cor": "#10b981", "url": "https://operacional.muralhapaulista.sp.gov.br"},
            {"titulo": "COPOM", "icone": "headset_mic", "cor": "#3b82f6", "url": "https://copomonline.policiamilitar.sp.gov.br"},
            {"titulo": "INFOSEG", "icone": "search", "cor": "#f59e0b", "url": "https://seguranca.sinesp.gov.br"}
        ]}
    ]
}

@app.route('/api/layout', methods=['GET'])
def get_layout():
    return jsonify(LAYOUT_APP)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    # Validação simples para teste (depois ativamos o admin_core)
    if data.get('usuario') and data.get('senha'):
        if core.validar_login_linux(data['usuario'], data['senha']):
            return jsonify({
                "sucesso": True,
                "ssh": {
                    "host": config.API_HOST if config.API_HOST != "0.0.0.0" else request.host.split(':')[0],
                    "port": config.SSH_PORT,
                    "user": data['usuario'],
                    "pass": data['senha']
                }
            })
    return jsonify({"sucesso": False, "mensagem": "Dados inválidos"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
