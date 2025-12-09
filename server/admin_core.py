
import paramiko
import config

class AdminCore:
    def validar_login_linux(self, usuario, senha):
        """
        Tenta conectar via SSH no localhost (127.0.0.1) para validar
        se o usuário e senha existem no sistema Linux.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Tenta conectar na própria máquina
            client.connect(
                hostname='127.0.0.1', 
                port=config.SSH_PORT, 
                username=usuario, 
                password=senha, 
                timeout=5
            )
            client.close()
            return True # Login aceito
        except Exception as e:
            # Se der erro de autenticação ou conexão
            return False
          
