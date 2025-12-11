from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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

app = FastAPI(title="PMESP VPS API", version="0.1.0")

# Cria as tabelas no banco ao iniciar
Base.metadata.create_all(bind=engine)


# ----------------------- Rotas básicas -----------------------

@app.get("/ping")
def ping():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


# ----------------------- Usuários -----------------------

@app.post("/users", response_model=UserRead)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Verifica se já existe
    existing = db.query(models.User).filter_by(username=user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    # Cria no Linux
    try:
        expires_at = criar_usuario_linux(
            username=user_in.username,
            senha=user_in.senha_linux,
            dias_validade=user_in.dias_validade
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário no Linux: {e}"
        )

    # Registra no banco
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


@app.get("/users", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@app.get("/users/{username}", response_model=UserRead)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@app.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
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
def update_validade(username: str, body: UserUpdateValidade, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        expires_at = alterar_validade_linux(username, body.novos_dias)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao alterar validade no Linux: {e}"
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
    db: Session = Depends(get_db)
):
    """Lista usuários vencidos ou que vencem em X dias (padrão 5)."""
    hoje = datetime.utcnow().date()
    limite = hoje + timedelta(days=days)

    users = db.query(models.User).all()
    result = []
    for u in users:
        d = u.expires_at.date()
        if d <= limite:
            result.append(u)
    return result


@app.post("/users/{username}/kick")
def kick(username: str):
    """Derruba o usuário imediatamente (todas as sessões)."""
    kick_user(username)
    return {"status": "ok", "message": f"Usuário {username} desconectado"}


# ----------------------- Sites -----------------------

@app.post("/sites", response_model=SiteRead)
def create_site(site_in: SiteCreate, db: Session = Depends(get_db)):
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
def list_sites(db: Session = Depends(get_db)):
    sites = db.query(models.Site).order_by(models.Site.id.asc()).all()
    return sites


# ----------------------- Auth / Check -----------------------

@app.post("/auth/check", response_model=LoginStatus)
def auth_check(body: LoginCheck, db: Session = Depends(get_db)):
    """Rota que o seu cliente Windows vai chamar antes de abrir o túnel SSH."""
    status = check_login_status(db, body)
    return status


# ----------------------- Monitor -----------------------

@app.get("/monitor/online", response_model=List[OnlineUser])
def monitor_online(db: Session = Depends(get_db)):
    """Lista usuários com sessões ativas (via comando who)."""
    return listar_usuarios_online(db)


# ----------------------- Tickets -----------------------

@app.post("/tickets", response_model=TicketRead)
def create_ticket_route(ticket_in: TicketCreate, db: Session = Depends(get_db)):
    try:
        ticket = create_ticket(db, ticket_in)
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/tickets", response_model=List[TicketRead])
def list_tickets_route(db: Session = Depends(get_db)):
    return list_tickets(db)
