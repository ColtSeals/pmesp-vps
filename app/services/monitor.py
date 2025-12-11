from typing import List
from sqlalchemy.orm import Session

from .. import models
from ..schemas import OnlineUser
from .linux_users import contar_sessoes_ssh


def listar_usuarios_online(db: Session) -> List[OnlineUser]:
    """Retorna lista de usuários com sessões ativas (via who)."""
    result: list[OnlineUser] = []

    users = db.query(models.User).all()
    for u in users:
        sessoes = contar_sessoes_ssh(u.username)
        if sessoes > 0:
            result.append(
                OnlineUser(
                    username=u.username,
                    sessions=sessoes,
                    session_limit=u.session_limit,
                )
            )
    return result
