from datetime import datetime
from sqlalchemy.orm import Session

from .. import models
from ..schemas import LoginCheck, LoginStatus, SiteInfo
from .linux_users import contar_sessoes_ssh


def check_login_status(db: Session, payload: LoginCheck) -> LoginStatus:
    """
    Centraliza a lógica de validação de login/HWID/limite/sítios.

    - Verifica se o usuário existe e está ativo
    - Verifica validade (dias restantes / expires_at)
    - Valida ou vincula HWID na primeira vez
    - Verifica limite de sessões SSH
    - Carrega a lista de sites permitidos
    """
    # 1) Usuário existe?
    user = db.query(models.User).filter_by(username=payload.username).first()
    if not user:
        return LoginStatus(ok=False, reason="NOT_FOUND")

    # 2) Está ativo?
    if not user.is_active:
        return LoginStatus(ok=False, reason="BLOCKED")

    # 3) Validade
    #    - Se expires_at for None (pré-cadastro), já trata como vencido
    if not user.expires_at:
        return LoginStatus(
            ok=False,
            reason="EXPIRED",
            dias_restantes=0,
            session_limit=user.session_limit,
        )

    hoje = datetime.utcnow().date()
    dias_restantes = (user.expires_at.date() - hoje).days

    if dias_restantes <= 0:
        return LoginStatus(
            ok=False,
            reason="EXPIRED",
            dias_restantes=0,
            session_limit=user.session_limit,
        )

    # 4) HWID: valida / vincula
    #    - Se já tem HWID diferente → bloqueia
    #    - Se não tem (ou está "PENDENTE") → vincula o HWID desta máquina
    hwid_atual = (user.hwid or "").strip()

    if hwid_atual and hwid_atual.upper() != "PENDENTE":
        # Já existe um HWID vinculado → tem que bater
        if hwid_atual != payload.hwid:
            return LoginStatus(
                ok=False,
                reason="HWID_MISMATCH",
                dias_restantes=dias_restantes,
                session_limit=user.session_limit,
            )
    else:
        # Não havia HWID, ou estava "PENDENTE" → grava o HWID desta máquina
        user.hwid = payload.hwid
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

    # 5) Conta sessões no Linux
    sessoes = contar_sessoes_ssh(user.username)
    if sessoes >= user.session_limit:
        return LoginStatus(
            ok=False,
            reason="LIMIT_REACHED",
            dias_restantes=dias_restantes,
            session_limit=user.session_limit,
        )

    # 6) Carrega sites permitidos:
    #    Se não houver mapeamento específico, libera TODOS os sites.
    from ..models import UserSite, Site  # import local para evitar loop circular

    user_sites = (
        db.query(UserSite)
        .filter_by(user_id=user.id, allowed=True)
        .all()
    )

    if user_sites:
        site_ids = [us.site_id for us in user_sites]
        sites = db.query(Site).filter(Site.id.in_(site_ids)).all()
    else:
        sites = db.query(Site).all()

    sites_info = [
        SiteInfo(
            slug=s.slug,
            name=s.name,
            url=s.url,
            status=s.default_status,
        )
        for s in sites
    ]

    # 7) Tudo certo → acesso liberado
      return LoginStatus(
        ok=True,
        reason=None,
        dias_restantes=dias_restantes,
        session_limit=user.session_limit,
        role=user.role,          # NOVO
        sites=sites_info,
    )
