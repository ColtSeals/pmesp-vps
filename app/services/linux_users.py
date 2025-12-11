import subprocess
from datetime import datetime, timedelta


def user_exists(username: str) -> bool:
    """Verifica se o usuário Linux existe."""
    try:
        subprocess.run(
            ["id", username],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def criar_usuario_linux(username: str, senha: str, dias_validade: int) -> datetime:
    """Cria usuário no Linux sem shell, define senha e validade.

    Retorna a data de expiração.
    """
    # cria usuário sem home (-M) e sem shell (/bin/false)
    subprocess.run(["useradd", "-M", "-s", "/bin/false", username], check=True)

    # define a senha
    p = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE)
    p.communicate(f"{username}:{senha}".encode())
    if p.returncode != 0:
        raise RuntimeError("Falha ao definir senha no Linux")

    # calcula data de validade
    data_final = datetime.utcnow() + timedelta(days=dias_validade)

    # configura validade com chage -E YYYY-MM-DD
    subprocess.run(
        ["chage", "-E", data_final.strftime("%Y-%m-%d"), username],
        check=True
    )

    return data_final


def alterar_validade_linux(username: str, novos_dias: int) -> datetime:
    """Altera a validade do usuário no Linux e retorna a nova data."""
    data_final = datetime.utcnow() + timedelta(days=novos_dias)
    subprocess.run(
        ["chage", "-E", data_final.strftime("%Y-%m-%d"), username],
        check=True
    )
    return data_final
def alterar_senha_linux(username: str, nova_senha: str) -> None:
    """
    Altera a senha do usuário no Linux via chpasswd.
    """
    if not user_exists(username):
        raise RuntimeError(f"Usuário Linux '{username}' não existe.")

    proc = subprocess.Popen(
        ["chpasswd"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    saida, erro = proc.communicate(f"{username}:{nova_senha}".encode())

    if proc.returncode != 0:
        raise RuntimeError(
            f"Falha ao alterar senha no Linux: {erro.decode().strip()}"
        )


def delete_user_linux(username: str) -> None:
    """Remove o usuário Linux (se existir)."""
    if not user_exists(username):
        return
    subprocess.run(["userdel", "-f", username], check=False)


def kick_user(username: str) -> None:
    """Derruba TODAS as sessões (SSH, etc.) do usuário."""
    # pkill -KILL -u username
    subprocess.run(["pkill", "-KILL", "-u", username], check=False)


def contar_sessoes_ssh(username: str) -> int:
    """Conta sessões do usuário usando o comando `who`.

    Não é perfeito, mas já dá uma boa visão.
    """
    try:
        out = subprocess.check_output(["who"], text=True)
    except Exception:
        return 0

    count = 0
    for line in out.splitlines():
        if line.startswith(username + " "):
            count += 1
    return count
