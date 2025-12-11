from datetime import datetime
from sqlalchemy.orm import Session

from .. import models
from ..schemas import LoginCheck, LoginStatus, SiteInfo
from .linux_users import contar_sessoes_ssh


def check_login_status(db: Session, payload: LoginCheck) -> LoginStatus:
    """Centraliza a lógica de validação de login/HWID/limite/sítios."""
    user = db.query(models.User).filter_by(username=payload.username).first()
    if not user:
        return LoginStatus(ok=False, reason="NOT_FOUND")

    if not user.is_active:
        return LoginStatus(ok=False, reason="BLOCKED")

    hoje = datetime.utcnow().date()
    dias_restantes = (user.expires_at.date() - hoje).days

    if dias_restantes <= 0:
        return LoginStatus(
            ok=False,
            reason="EXPIRED",
            dias_restantes=0,
            session_limit=user.session_limit
        )

    # valida / vincula HWID
    if user.hwid and user.hwid != payload.hwid:
        return LoginStatus(
            ok=False,
            reason="HWID_MISMATCH",
            dias_restantes=dias_restantes,
            session_limit=user.session_limit
        )

    if not user.hwid:
        user.hwid = payload.hwid
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)

    # Conta sessões no Linux
    sessoes = contar_sessoes_ssh(user.username)
    if sessoes >= user.session_limit:
        return LoginStatus(
            ok=False,
            reason="LIMIT_REACHED",
            dias_restantes=dias_restantes,
            session_limit=user.session_limit
        )

    # Carrega sites permitidos:
    # Se não houver mapeamento específico, libera TODOS os sites.
    from ..models import UserSite, Site  # import local para evitar loop

    user_sites = db.query(UserSite).filter_by(user_id=user.id, allowed=True).all()
    if user_sites:
        site_ids = [us.site_id for us in user_sites]
        sites = db.query(Site).filter(Site.id.in_(site_ids)).all()
    else:
        sites = db.query(Site).all()

    sites_info = [
        SiteInfo(slug=s.slug, name=s.name, url=s.url, status=s.default_status)
        for s in sites
    ]

    return LoginStatus(
        ok=True,
        reason=None,
        dias_restantes=dias_restantes,
        session_limit=user.session_limit,
        sites=sites_info
    )
