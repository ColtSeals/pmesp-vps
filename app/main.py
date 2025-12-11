import os
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from .db import Base, engine, get_db
from . import models
from .schemas import (
    UserCreate, UserRead, UserUpdateValidade,
    SiteCreate, SiteRead,
    LoginCheck, LoginStatus,
    TicketCreate, TicketRead,
    OnlineUser,
)
from .services.linux_users import (
    criar_usuario_linux,
    alterar_validade_linux,
    delete_user_linux,
    kick_user,
)
from .services.auth import check_login_status
from .services.monitor import listar_usuarios_online
from .services.tickets import create_ticket, list_tickets


# --------------------------------------------------------------------
# CONFIGURAÇÃO DE SEGURANÇA (TOKEN DE ADMIN)
# --------------------------------------------------------------------

ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")

api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def require_admin(api_key: str = Security(api_key_header)):
    """
    Essa função será usada como dependência das rotas de administrador.
    Verifica se o header X-Admin-Token bate com o valor configurado.
    """
    if not api_key or api_key != ADMIN_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Não autorizado (admin token inválido)"
        )


# --------------------------------------------------------------------
# Pydantic extras (somente para esse arquivo)
# --------------------------------------------------------------------

class PublicRegister(BaseModel):
    """
    Pré-cadastro público (sem token de admin).
    Cria um usuário pendente, sem validade e bloqueado.
    Já armazena o HWID da máquina.
    """
    username: str
    matricula: str
    email: EmailStr
    hwid: str


class UserActivate(BaseModel):
    """
    Corpo para ativação de um usuário pré-cadastrado.
    O admin define:
      - dias de validade
      - limite de sessões
      - papel (role)
      - senha Linux
    """
    dias_validade: int
    session_limit: int = 1
    role: str = "user"
    senha_linux: str


# --------------------------------------------------------------------
# INICIALIZAÇÃO DO APP
# --------------------------------------------------------------------

app = FastAPI(title="PMESP VPS API", version="0.1.0")

# Cria as tabelas no banco ao iniciar
Base.metadata.create_all(bind=engine)


# ----------------------- Rotas públicas -----------------------

@app.get("/ping")
def ping():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/auth/check", response_model=LoginStatus)
def auth_check(body: LoginCheck, db: Session = Depends(get_db)):
    """
    Rota que o cliente Windows chama antes de abrir o túnel SSH.
    (rota pública - não exige token de admin)
    """
    status = check_login_status(db, body)
    return status


@app.post("/public/register")
def public_register(body: PublicRegister, db: Session = Depends(get_db)):
    """
    Pré-cadastro público de usuário.
    - Não cria usuário no Linux ainda.
    - Salva username, matrícula, email, HWID.
    - Fica com dias_validade=0, expires_at=None, is_active=False.
    Depois o admin precisa chamar /users/{username}/activate.
    """
    existing = db.query(models.User).filter_by(username=body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    now = datetime.utcnow()

    user = models.User(
        username=body.username,
        matricula=body.matricula,
        email=body.email,
        hwid=body.hwid,
        dias_validade=0,
        expires_at=None,          # ainda não liberado
        session_limit=1,
        role="user",
        is_active=False,          # bloqueado até o gestor ativar
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "status": "ok",
        "message": "Pré-cadastro recebido. Aguarde liberação do gestor.",
        "username": user.username,
    }


# ----------------------- Usuários (ADMIN) -----------------------

@app.post("/users", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """
    Cria usuário COMPLETO:
      - cria no Linux
      - grava no banco como ativo
    (fluxo clássico, sem pré-cadastro).
    """
    existing = db.query(models.User).filter_by(username=user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    # Cria no Linux
    try:
        expires_at = criar_usuario_linux(
            username=user_in.username,
            senha=user_in.senha_linux,
            dias_validade=user_in.dias_validade,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário no Linux: {e}",
        )

    now = datetime.utcnow()
    user = models.User(
        username=user_in.username,
        matricula=user_in.matricula,
        email=user_in.email,
        dias_validade=user_in.dias_validade,
        expires_at=expires_at,
        session_limit=user_in.session_limit,
        role=user_in.role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/users/{username}/activate", response_model=UserRead)
def activate_user(
    username: str,
    body: UserActivate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    """
    Ativa um usuário PRÉ-CADASTRADO (criado via /public/register).
    - Cria usuário no Linux
    - Define validade, limite, role
    - Marca como ativo
    """
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.expires_at is not None:
        raise HTTPException(
            status_code=400,
            detail="Usuário já possui validade (provavelmente já está ativo).",
        )

    try:
        expires_at = criar_usuario_linux(
            username=user.username,
            senha=body.senha_linux,
            dias_validade=body.dias_validade,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário no Linux: {e}",
        )

    user.dias_validade = body.dias_validade
    user.expires_at = expires_at
    user.session_limit = body.session_limit
    user.role = body.role
    user.is_active = True
    user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=List[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@app.get("/users/{username}", response_model=UserRead)
def get_user(
    username: str,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@app.delete("/users/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # remove do Linux
    delete_user_linux(username)

    # remove do banco
    db.delete(user)
    db.commit()

    return {"status": "ok", "message": f"Usuário {username} removido"}


@app.patch("/users/{username}/validade", response_model=UserRead)
def update_validade(
    username: str,
    body: UserUpdateValidade,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        expires_at = alterar_validade_linux(username, body.novos_dias)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao alterar validade no Linux: {e}",
        )

    user.dias_validade = body.novos_dias
    user.expires_at = expires_at
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/expiring", response_model=List[UserRead])
def list_expiring(
    days: int = Query(5, ge=1, le=365),
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    """Lista usuários vencidos ou que vencem em X dias (padrão 5)."""
    hoje = datetime.utcnow().date()
    limite = hoje + timedelta(days=days)

    users = db.query(models.User).all()
    result = []
    for u in users:
        if not u.expires_at:
            continue
        d = u.expires_at.date()
        if d <= limite:
            result.append(u)
    return result


@app.post("/users/{username}/kick")
def kick(
    username: str,
    _admin: None = Depends(require_admin),
):
    """Derruba o usuário imediatamente (todas as sessões)."""
    kick_user(username)
    return {"status": "ok", "message": f"Usuário {username} desconectado"}


# ----------------------- Sites (ADMIN) -----------------------

@app.post("/sites", response_model=SiteRead)
def create_site(
    site_in: SiteCreate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    existing = db.query(models.Site).filter_by(slug=site_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug já existe")

    site = models.Site(
        slug=site_in.slug,
        name=site_in.name,
        url=site_in.url,
        icon=site_in.icon,
        default_status=site_in.default_status,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@app.get("/sites", response_model=List[SiteRead])
def list_sites(
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    sites = db.query(models.Site).order_by(models.Site.id.asc()).all()
    return sites


# ----------------------- Monitor (ADMIN) -----------------------

@app.get("/monitor/online", response_model=List[OnlineUser])
def monitor_online(
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    """Lista usuários com sessões ativas (via comando who)."""
    return listar_usuarios_online(db)


# ----------------------- Tickets (ADMIN) -----------------------

@app.post("/tickets", response_model=TicketRead)
def create_ticket_route(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    try:
        ticket = create_ticket(db, ticket_in)
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/tickets", response_model=List[TicketRead])
def list_tickets_route(
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    return list_tickets(db)
