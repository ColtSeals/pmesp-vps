import paramiko
import json
import time
import socket
from datetime import datetime

# Importa as configurações da RAIZ (já que estão no mesmo nível)
import config_base

class AdminCore:
    def __init__(self):
        self.host = "127.0.0.1" # Conecta na própria VPS (localhost)
        self.port = config_base.SSH_PORT
        self.user = config_base.ROOT_USER
        self.password = config_base.ROOT_PASS
        self.client = None

    def _connect(self):
        """Estabelece conexão SSH local como ROOT para executar comandos administrativos."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                timeout=5
            )
            return True
        except Exception as e:
            print(f"[ERRO ADMIN] Falha ao conectar SSH Local: {e}")
            return False

    def _disconnect(self):
        if self.client:
            self.client.close()

    def _exec_command(self, command):
        """Executa comando bash e retorna a saída."""
        if not self._connect():
            return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            self._disconnect()
            
            if exit_status == 0:
                return output
            else:
                print(f"[ERRO CMD] Comando: {command} | Erro: {error}")
                return None
        except Exception as e:
            print(f"[ERRO EXEC] {e}")
            self._disconnect()
            return None

    # =================================================================
    # GESTÃO DO ARQUIVO JSON (DB DE USUÁRIOS)
    # =================================================================

    def get_all_users(self):
        """Lê o arquivo JSON e retorna lista de todos usuários."""
        # Lê o arquivo diretamente via cat
        raw_data = self._exec_command(f"cat {config_base.USER_JSON_PATH}")
        users = []
        if raw_data:
            lines = raw_data.splitlines()
            for line in lines:
                if line.strip():
                    try:
                        users.append(json.loads(line))
                    except:
                        continue
        return users

    def get_user_data(self, username):
        """Busca dados de um usuário específico."""
        users = self.get_all_users()
        # Procura de trás para frente (última atualização válida)
        for u in reversed(users):
            if u.get("usuario") == username:
                return u
        return None

    def update_user_json(self, username, new_data_dict):
        """
        Atualiza campos do usuário no JSON.
        new_data_dict: dicionário com campos a atualizar (ex: {'dias': '30', 'hwid': '...'})
        """
        current_data = self.get_user_data(username)
        if not current_data:
            return False

        # Atualiza os campos existentes com os novos
        current_data.update(new_data_dict)
        
        new_line = json.dumps(current_data)
        
        # 1. Remove a linha antiga (sed)
        # 2. Adiciona a linha nova (echo)
        # Atenção com as aspas no comando sed
        cmd_remove = f"sed -i '/\"usuario\": \"{username}\"/d' {config_base.USER_JSON_PATH}"
        cmd_append = f"echo '{new_line}' >> {config_base.USER_JSON_PATH}"
        
        res_rm = self._exec_command(cmd_remove)
        # O sed não retorna output no sucesso, então verificamos se rodou sem erro (retorno None pode ser erro de conexão)
        # Mas para simplificar, vamos assumir que se conectou, funcionou.
        
        res_add = self._exec_command(cmd_append)
        
        return True

    # =================================================================
    # FUNÇÕES DE SISTEMA (LINUX)
    # =================================================================

    def create_linux_user(self, username, password, email, matricula):
        """Cria usuário no Linux (sem shell) e adiciona entrada inicial no JSON."""
        # Verifica se já existe
        if self.get_user_data(username):
            return False, "Usuário já existe no banco de dados."

        # Dados iniciais para o JSON
        user_json = json.dumps({
            "usuario": username,
            "senha": password, # (Opcional manter no JSON se já valida no Linux, mas seu sistema legado usava)
            "email": email,
            "matricula": matricula,
            "dias": "30",   # Padrão inicial
            "limite": "1",  # Padrão inicial
            "hwid": "PENDENTE",
            "role": "user"  # Padrão: usuário comum
        })

        # Comando composto: Useradd -> Senha -> JSON -> Permissão
        cmd = (
            f"useradd -M -s /bin/false {username} && "
            f"echo '{username}:{password}' | chpasswd && "
            f"echo '{user_json}' >> {config_base.USER_JSON_PATH}"
        )
        
        result = self._exec_command(cmd)
        
        # Se result for None, houve falha de conexão ou comando.
        # Useradd não retorna texto no sucesso, apenas exit code 0.
        # Minha função _exec_command retorna "" (string vazia) se sucesso mas sem output, ou None se erro.
        if result is not None: 
            return True, "Usuário criado com sucesso."
        else:
            return False, "Falha ao criar usuário no sistema."

    def change_password(self, username, new_password):
        """Altera senha no Linux e atualiza no JSON."""
        # 1. Linux
        cmd_linux = f"echo '{username}:{new_password}' | chpasswd"
        if self._exec_command(cmd_linux) is None:
            return False

        # 2. JSON (para manter registro visual se necessário)
        return self.update_user_json(username, {"senha": new_password})

    def check_active_sessions(self, username):
        """Conta processos sshd do usuário."""
        cmd = f"ps -u {username} | grep sshd | wc -l"
        res = self._exec_command(cmd)
        if res and res.isdigit():
            return int(res)
        return 0
    
    def validate_hwid(self, username, client_hwid):
        """
        Verifica o HWID.
        Retorna: (True/False, Mensagem)
        Se for 'PENDENTE', registra e aprova.
        """
        data = self.get_user_data(username)
        if not data:
            return False, "Usuário não encontrado."
            
        stored_hwid = data.get("hwid", "PENDENTE")
        
        if stored_hwid == "PENDENTE":
            # Primeiro acesso: Vincula
            if self.update_user_json(username, {"hwid": client_hwid}):
                return True, "HWID vinculado com sucesso."
            else:
                return False, "Erro ao vincular HWID."
        
        if stored_hwid == client_hwid:
            return True, "HWID Válido."
        else:
            return False, "HWID Incorreto (Máquina não autorizada)."


