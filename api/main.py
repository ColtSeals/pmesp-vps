import json
import subprocess
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Caminho do banco de dados
DB_FILE = "/etc/pmesp_users.json"

class LoginModel(BaseModel):
    usuario: str
    senha: str
    hwid: str

def ler_usuarios():
    """
    Lê o arquivo JSON de forma robusta.
    Funciona tanto se o Bash salvou em uma linha (compacto)
    quanto se salvou em várias linhas (pretty print).
    """
    usuarios = []

    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r") as f:
            conteudo = f.read().strip()

            if not conteudo:
                return []

            # Decodificador inteligente que lê múltiplos objetos JSON concatenados
            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(conteudo):
                # Pula espaços em branco (quebras de linha, espaços)
                while pos < len(conteudo) and conteudo[pos].isspace():
                    pos += 1

                if pos >= len(conteudo):
                    break

                try:
                    # Tenta extrair o próximo objeto JSON válido
                    obj, end_pos = decoder.raw_decode(conteudo, pos)
                    usuarios.append(obj)
                    pos = end_pos
                except json.JSONDecodeError:
                    # Se achar lixo no arquivo, pula 1 caractere e tenta de novo
                    pos += 1

    except Exception as e:
        print(f"Erro ao ler banco de dados: {e}")
        return []

    return usuarios

@app.post("/auth")
def autenticar(dados: LoginModel):
    print(f"--> Recebido login: {dados.usuario} | Senha: {dados.senha}")

    users = ler_usuarios()
    print(f"--> Usuários carregados do banco: {len(users)}")

    # Busca o usuário (ignora maiúsculas/minúsculas)
    user_encontrado = next((u for u in users if u.get("usuario", "").lower() == dados.usuario.lower()), None)

    if not user_encontrado:
        print("--> Falha: Usuário não encontrado na lista.")
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    # 1. Verifica Senha
    senha_db = str(user_encontrado.get("senha", "")).strip()
    senha_input = str(dados.senha).strip()

    if senha_db != senha_input:
        print("--> Falha: Senha incorreta.")
        raise HTTPException(status_code=401, detail="Senha incorreta")

    # 2. Verifica HWID
    hwid_db = user_encontrado.get("hwid", "PENDENTE")

    # Lógica de Primeiro Acesso: Se for PENDENTE, libera (Auto-Vinculo seria feito aqui se quisesse)
    if hwid_db != "PENDENTE" and hwid_db != dados.hwid:
         print(f"--> Falha HWID: Banco={hwid_db} vs App={dados.hwid}")
         raise HTTPException(status_code=403, detail="Computador não autorizado (HWID)")

    # 3. SUCESSO
    print(f"--> SUCESSO: {dados.usuario} logado.")
    return {
        "status": "aprovado",
        "usuario": user_encontrado['usuario'],
        "tunnel_port": 443,
        "proxy_port": 40000,
        "mensagem": "Conectado"
    }
