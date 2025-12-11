from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    matricula = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    hwid = Column(String(255), nullable=True)  # HWID da máquina
    dias_validade = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True)  # no pré-cadastro pode ficar None
    session_limit = Column(Integer, nullable=False, default=1)
    role = Column(String(50), nullable=False, default="user")   # 'admin', 'user', etc.
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # relações
    sites = relationship("UserSite", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)  # 'copom', 'muralha'
    name = Column(String(100), nullable=False)                          # nome exibido
    url = Column(String(500), nullable=False)
    icon = Column(String(50), nullable=True)                            # nome do ícone (opcional)
    default_status = Column(String(20), nullable=False, default="ONLINE")  # ONLINE/OFFLINE/LENTO

    users = relationship("UserSite", back_populates="site", cascade="all, delete-orphan")


class UserSite(Base):
    __tablename__ = "user_sites"
    __table_args__ = (UniqueConstraint("user_id", "site_id", name="uq_user_site"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    allowed = Column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="sites")
    site = relationship("Site", back_populates="users")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    status = Column(String(20), nullable=False, default="ABERTO")  # ABERTO/ENCERRADO/etc
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="tickets")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)  # ex: UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_hwid = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_ping = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="sessions")
