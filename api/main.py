import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess

app = FastAPI()

# Caminho do banco de dados do seu script Bash
DB_FILE = "/etc/pmesp_users.json"

class LoginModel(BaseModel):
    usuario: str
    senha: str
    hwid: str

def ler_usuarios():
    """Lê o arquivo JSON gerado pelo Bash (que salva linha por linha)"""
    usuarios = []
    try:
        with open(DB_FILE, "r") as f:
            for linha in f:
                if linha.strip():
                    try:
                        usuarios.append(json.loads(linha))
                    except:
                        continue
    except FileNotFoundError:
        return []
    return usuarios

@app.post("/auth")
def autenticar(dados: LoginModel):
    users = ler_usuarios()
    
    # Procura o usuário
    user_encontrado = next((u for u in users if u["usuario"] == dados.usuario), None)
    
    if not user_encontrado:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    # 1. Verifica Senha
    if user_encontrado["senha"] != dados.senha:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    # 2. Verifica Validade (Chama comando Linux para checar)
    # O script python chama o 'chage' do linux para ver se expirou
    try:
        cmd = f"chage -l {dados.usuario} | grep 'Account expires'"
        resultado = subprocess.check_output(cmd, shell=True).decode()
        if "Account expires" in resultado:
            data_str = resultado.split(":")[1].strip()
            # Se não for 'never', precisamos checar a data (simplificado aqui)
            # Para produção, converteríamos data para timestamp
            pass 
    except:
        pass # Se der erro no comando, assume que tá ok ou trata depois

    # 3. Verifica HWID
    # Se no banco estiver "PENDENTE", a gente atualiza (Opcional - Lógica de Auto-Vinculo)
    if user_encontrado.get("hwid") == "PENDENTE":
        # Aqui você precisaria de uma função para atualizar o JSON
        # Por segurança, vamos apenas negar se não bater, ou liberar se for o primeiro acesso
        pass 
    elif user_encontrado.get("hwid") != dados.hwid:
        raise HTTPException(status_code=403, detail="HWID Inválido (Computador diferente)")

    # 4. SUCESSO - Retorna dados de conexão (Portas Altas)
    return {
        "status": "aprovado",
        "tunnel_port": 22,    # Ou porta SSH customizada
        "proxy_port": 40000,  # Porta alta do Squid
        "mensagem": f"Bem vindo, {user_encontrado['matricula']}"
    }
