from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------- USERS ----------

class UserBase(BaseModel):
    username: str
    matricula: str
    email: EmailStr
    dias_validade: int
    session_limit: int = 1
    role: str = "user"


class UserCreate(UserBase):
    # Senha usada para criar o usuário no Linux
    senha_linux: str


class UserRead(BaseModel):
    id: int
    username: str
    matricula: str
    email: EmailStr
    dias_validade: int
    expires_at: datetime
    session_limit: int
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class UserUpdateValidade(BaseModel):
    novos_dias: int


# ---------- SITES ----------

class SiteBase(BaseModel):
    slug: str
    name: str
    url: str
    icon: Optional[str] = None
    default_status: str = "ONLINE"


class SiteCreate(SiteBase):
    pass


class SiteRead(SiteBase):
    id: int

    class Config:
        orm_mode = True


# ---------- AUTH / LOGIN ----------

class LoginCheck(BaseModel):
    username: str
    hwid: str   # HWID da máquina do usuário


class SiteInfo(BaseModel):
    slug: str
    name: str
    url: str
    status: str


class LoginStatus(BaseModel):
    ok: bool
    reason: Optional[str] = None
    dias_restantes: Optional[int] = None
    session_limit: Optional[int] = None
    sites: Optional[List[SiteInfo]] = None


# ---------- MONITOR ----------

class OnlineUser(BaseModel):
    username: str
    sessions: int
    session_limit: int


# ---------- TICKETS ----------

class TicketCreate(BaseModel):
    username: str
    title: str
    description: str


class TicketRead(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
