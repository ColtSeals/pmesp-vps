from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./pmesp_system.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String) # Nunca salvamos senha pura
    matricula = Column(String)
    email = Column(String)
    hwid = Column(String, default="PENDENTE")
    valid_until = Column(DateTime) # Data de validade
    max_sessions = Column(Integer, default=1)
    access_level = Column(Integer, default=1) # 1=Básico, 2=Copom, 3=Full, 99=Admin
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    site_accessed = Column(String)
    captured_login = Column(String)
    captured_password = Column(String) # Auditoria de segurança
    timestamp = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)
