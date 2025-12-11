1. Clonar o repositório

No SSH da sua VPS (de preferência logado como root):

# Se ainda não tiver o git:
apt-get update -y
apt-get install -y git

# Entrar numa pasta onde você guarda projetos (ex: /root)
cd /root

# Clonar o repositório
git clone https://github.com/ColtSeals/pmesp-vps.git

# Entrar na pasta do projeto
cd pmesp-vps

2. Tornar o setup.sh executável
chmod +x app/services/setup.sh

3. Rodar o script de setup

Ele vai instalar Python, criar o venv e instalar as libs da API.

bash app/services/setup.sh
# ou, se preferir:
# ./app/services/setup.sh


Se tudo der certo, no final ele deve mostrar algo como:

[OK] Ambiente pronto!
Para iniciar a API, rode:
  source venv/bin/activate
  uvicorn app.main:app --host 0.0.0.0 --port 8000

4. Subir a API

Ainda dentro da pasta pmesp-vps:

# Ativar o ambiente virtual
source venv/bin/activate

# Subir a API
uvicorn app.main:app --host 0.0.0.0 --port 8000


Deixa esse comando rodando (ele mostra logs no terminal).

5. Testar se está funcionando

No mesmo servidor, em outro SSH ou abrindo outra aba:

cd /root/pmesp-vps
source venv/bin/activate

curl http://127.0.0.1:8000/ping


Se aparecer algo assim:

{"status":"ok","time":"2025-..."}


✅ API está no ar.

Se você acessar do seu computador:

http://IP_DA_VPS:8000/ping


no navegador, deve ver o mesmo JSON (se a porta 8000 estiver liberada no firewall).

6. Resumindo os comandos principais

Pra não se perder:

# 1x na vida (ou quando formatar VPS)
apt-get update -y
apt-get install -y git
git clone https://github.com/ColtSeals/pmesp-vps.git
cd pmesp-vps
chmod +x app/services/setup.sh
bash app/services/setup.sh

# Sempre que for ligar a API depois
cd /root/pmesp-vps
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000


Se você rodar isso e me contar:

deu erro em alguma linha?

o /ping respondeu?

aí no próximo passo eu já te ensino a:

cadastrar um site padrão (COPOM, MURALHA etc.)

criar um usuário via API

e depois plugamos isso no seu cliente Flet.

Você disse:
{"status":"ok","time":"2025-12-11T04:09:51.701358"}
O ChatGPT disse:
Pensou por 14s

PERFEITO 🥳
Isso aí que você me mandou:

{"status":"ok","time":"2025-12-11T04:09:51.701358"}


significa:

✅ API está rodando certinho na VPS.

Agora vamos pro próximo nível: usar essa API pra criar sites e usuários, tudo pelo navegador, sem precisar decorar curl.

1. Abrir o painel automático da API (Swagger)

No seu computador, abre o navegador e entra em:

http://IP_DA_SUA_VPS:8000/docs


Exemplo: se sua VPS for 147.79.110.50:

http://147.79.110.50:8000/docs


Você vai ver uma tela azul da FastAPI com todas as rotas:

/ping

/users

/sites

/auth/check

/monitor/online

/tickets

etc.

Ali você consegue testar tudo clicando, sem programar.

Se não abrir:

confere se o uvicorn ainda está rodando na VPS

vê se a porta 8000 está liberada no firewall.

2. Cadastrar os sites padrão (COPOM, MURALHA, etc.)
2.1. No /docs, ache a seção sites

Vai aparecer:

POST /sites

GET /sites

Clica em POST /sites.

Clica em “Try it out”.

No Request body vai aparecer um JSON pra preencher.

Vamos cadastrar alguns exemplos.
Primeiro, COPOM:

{
  "slug": "copom",
  "name": "COPOM ONLINE",
  "url": "https://copomonline.policiamilitar.sp.gov.br/Login/Login",
  "icon": "headset_mic_outlined",
  "default_status": "ONLINE"
}


Clica em Execute.

Se der 200 e retornar o mesmo JSON com id, beleza.

Repete para os outros:

MURALHA:

{
  "slug": "muralha",
  "name": "MURALHA PAULISTA",
  "url": "https://operacional.muralhapaulista.sp.gov.br/Home/Login",
  "icon": "camera_alt_outlined",
  "default_status": "ONLINE"
}


INFOSEG:

{
  "slug": "infoseg",
  "name": "INFOSEG",
  "url": "https://seguranca.sinesp.gov.br/sinesp-seguranca/login.jsf?goto=INFOSEG",
  "icon": "search",
  "default_status": "LENTO"
}


FOTOCRIM:

{
  "slug": "fotocrim",
  "name": "FOTOCRIM",
  "url": "https://inteligenciaweb.intranet.policiamilitar.sp.gov.br/#/login",
  "icon": "face_retouching_natural",
  "default_status": "ONLINE"
}


INFOCRIM:

{
  "slug": "infocrim",
  "name": "INFOCRIM",
  "url": "https://www.infocrim.ssp.sp.gov.br/login",
  "icon": "videocam_off_outlined",
  "default_status": "OFFLINE"
}


Depois, você pode conferir tudo indo em GET /sites → Try it out → Execute.

3. Criar um usuário pelo painel /users

Esse usuário vai existir:

no Linux (para SSH)

e no banco de dados (para regras, HWID, limite, etc.)

3.1. No /docs, ache a seção users

Clica em POST /users → Try it out.

No corpo (Request body), coloca algo assim:

{
  "username": "soldado1",
  "matricula": "123456",
  "email": "soldado1@exemplo.pm",
  "dias_validade": 30,
  "session_limit": 1,
  "role": "user",
  "senha_linux": "SenhaForte123"
}


username: login que ele vai usar tanto no SSH quanto no seu app.

senha_linux: senha que vai ser cadastrada no Linux (SSH).

dias_validade: quantos dias de acesso.

session_limit: quantas conexões simultâneas (telas) você permite.

ATENÇÃO:
Esse endpoint roda useradd, chpasswd, chage.
Então o uvicorn precisa estar rodando como um usuário que tem permissão (normalmente root).

Se aparecer erro tipo “permission denied” ou algo com useradd, me conta depois.

Se der certo, vai voltar um JSON com o usuário criado.

Você pode listar usuários em GET /users → Execute.

4. Testar a rota de auth/check (o que o cliente Windows vai usar)

Essa rota é que vai dizer pro seu app:

se o usuário está ok / vencido / HWID errado / limite estourado;

quais sites ele pode acessar (por enquanto: todos os cadastrados).

4.1. No /docs, vá em POST /auth/check

Clica em Try it out.

No corpo, coloca:

{
  "username": "soldado1",
  "hwid": "TESTE-HWID-123"
}


O hwid é o ID da máquina. No seu app Windows a gente vai mandar o HWID real; aqui é só teste.

Se o usuário estiver válido, você deve ver algo assim:

{
  "ok": true,
  "reason": null,
  "dias_restantes": 29,
  "session_limit": 1,
  "sites": [
    { "slug": "muralha", "name": "MURALHA PAULISTA", "url": "...", "status": "ONLINE" },
    { "slug": "copom", "name": "COPOM ONLINE", "url": "...", "status": "ONLINE" },
    ...
  ]
}


Se algo estiver errado (HWID, vencido, limite, etc.), vem:

{
  "ok": false,
  "reason": "HWID_MISMATCH",
  ...
}


Isso é exatamente o que o seu cliente Flet vai usar para decidir se deixa logar, qual mensagem mostra, e quais cards de site mostrar.

5. Ver quem está online (quando tiver SSH)

Depois, quando você começar a conectar com o usuário via SSH, a rota:

GET /monitor/online

vai usar o comando who e mostrar:

[
  {
    "username": "soldado1",
    "sessions": 1,
    "session_limit": 1
  }
]


Por enquanto provavelmente vai vir [] (lista vazia), porque você ainda não abriu nenhuma sessão SSH com esse usuário.

6. Próximo passo (quando você me disser “ok, criei usuário e sites”)

Aí a próxima etapa vai ser:

Ajustar o cliente Flet pra:

na tela de login, chamar POST /auth/check com username + HWID;

se ok=true, aí sim tentar o SSH com paramiko usando a senha digitada;

usar os sites retornados para montar os cards e abrir o Firefox portátil.

Depois disso, a gente cria endpoints para:

definir quais sites cada usuário pode ou não pode acessar (perfis);

usar /users/{username}/kick pra expulsar aquele usuário imediatamente;

usar /users/expiring?days=5 pra ver quem está prestes a vencer.

Por enquanto, faz assim:

Abre http://IP_DA_VPS:8000/docs.

Cadastra os 5 sites.

Cadastra um usuário.

Testa POST /auth/check com esse usuário.

Quando tiver feito isso (ou aparecer algum erro na tela azul do /docs), me manda:

qual rota deu erro,

o texto do erro que aparece (aquele “detail”: "...").

Aí eu ajusto o que precisar e a gente parte pro lado do cliente Windows 🚓💻

Você disse:
eu fiquei preocupado por que as pessoas sem login conseguem alterar tudo isso?
O ChatGPT disse:
Pensou por 33s

Boa, ótima preocupação — e você tá certíssimo em se preocupar com isso ⚠️

Sim: do jeito que está agora, QUALQUER pessoa que acessar http://IP_DA_VPS:8000/docs consegue:

criar usuário Linux,

deletar usuário,

mudar validade,

etc.

Porque ainda não colocamos nenhum tipo de login na API.

Vamos arrumar isso agora.

Objetivo

Proteger as rotas “de administrador” com uma chave secreta (token).

Só quem souber essa chave consegue usar:

/users (criar, listar, remover, alterar validade…)

/sites

/monitor/online

/tickets

Deixar aberto só:

/ping (teste)

/auth/check (que será usada pelo seu app Windows)

Depois, se quiser, a gente também coloca proteção em /auth/check — mas o mais perigoso são as rotas que mexem em usuário no Linux.

Passo 1 – Definir um “token de admin” (senha da API)

Vamos usar uma variável de ambiente chamada PMESP_ADMIN_TOKEN.

No terminal da VPS, antes de subir a API, você vai rodar:

export PMESP_ADMIN_TOKEN="UM_TOKEN_BEM_GRANDE_E_SECRETO_AQUI"


Exemplo (não use exatamente esse, faz o seu):

export PMESP_ADMIN_TOKEN="Na0V4z4EssaChav3PraNinguem!"


Mais pra frente a gente pode colocar isso num arquivo tipo /etc/pmesp.env, mas por enquanto assim já funciona.

Passo 2 – Alterar o main.py para exigir esse token

Agora vamos atualizar o app/main.py inteiro com a versão abaixo, já incluindo a proteção.

Pode simplesmente substituir o conteúdo atual de app/main.py por esse aqui:

import os
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
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

# --------------------------------------------------------------------
# CONFIGURAÇÃO DE SEGURANÇA (TOKEN DE ADMIN)
# --------------------------------------------------------------------

# Lê o token do ambiente (export PMESP_ADMIN_TOKEN="...").
# Se não tiver setado, usa um valor padrão (mas é MUITO importante trocar isso!)
ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")

# Definimos um header HTTP chamado X-Admin-Token
api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def require_admin(api_key: str = Security(api_key_header)):
    """
    Essa função será usada como "dependência" das rotas de administrador.
    Ela verifica se o header X-Admin-Token bate com o valor configurado.
    """
    if not api_key or api_key != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Não autorizado (admin token inválido)")


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
    Rota que o seu cliente Windows vai chamar antes de abrir o túnel SSH.
    (rota pública - não exige token de admin)
    """
    status = check_login_status(db, body)
    return status


# ----------------------- Usuários (ADMIN) -----------------------

@app.post("/users", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
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
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
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

Passo 3 – Reiniciar a API com o token

Pare o uvicorn atual (Ctrl + C no terminal onde ele está rodando).

No terminal:

cd /root/pmesp-vps   # ou a pasta onde está o projeto

# ativa o venv
source venv/bin/activate

# define o token de admin (troca pela sua senha secreta)
export PMESP_ADMIN_TOKEN="Na0V4z4EssaChav3PraNinguem!"

# sobe a API
uvicorn app.main:app --host 0.0.0.0 --port 8000

Passo 4 – Como usar o token no /docs

Abra http://IP_DA_VPS:8000/docs de novo.

Clique em qualquer rota protegida, por exemplo GET /users.

Clique em Try it out.

Agora você vai ver um campo novo “X-Admin-Token” nos parâmetros.

Escreva exatamente o token que você exportou:

Na0V4z4EssaChav3PraNinguem!


Aí sim clique em Execute.

Se você tentar sem o header ou com valor errado, vai ver:

{"detail": "Não autorizado (admin token inválido)"}


Ou seja: qualquer pessoa que achar seu IP e abrir /docs vai ver a interface, mas não vai conseguir fazer nada sem esse token.

Extra: reforço de segurança (opcional)

Depois, se você quiser blindar mais ainda, dá pra:

Travar a porta 8000 no firewall (ufw) para só aceitar do seu IP.

Colocar um nginx na frente com HTTPS.

Mas só o token já é um salto gigantesco em segurança comparado ao que estava.

Se quiser, na próxima mensagem você pode me falar:

Conseguiu acessar /docs de novo?

Quando tenta GET /users sem token, ele bloqueia?

E quando manda o header X-Admin-Token certo, funciona?

Aí seguimos pra parte do cliente Windows usando /auth/check e depois configuramos os perfis de acesso pros sites.

Você disse:
calma vou formatar a vps como ficaria para eu colocar esse token so de exemplo no github so para teste mesmo... criar um arquivo ou alterar?
O ChatGPT disse:
Pensou por 18s

Boa pergunta, e é MUITO bom você já estar preocupado com isso 👏

Resumo rápido

Não precisa mudar nada na API pra usar um token de teste.

Você não deve colocar o token real no GitHub.

A gente deixa um token de exemplo no código, só pra desenvolvimento.

Na VPS “de verdade” você sobrescreve com uma variável de ambiente.

Vou te mostrar o jeito certinho.

1. Como o token está hoje no main.py

Na versão que te passei do app/main.py tem isso aqui no topo:

import os
...
# Lê o token do ambiente (export PMESP_ADMIN_TOKEN="...").
# Se não tiver setado, usa um valor padrão (mas é MUITO importante trocar isso!)
ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")


Isso significa:

Se existir a variável de ambiente PMESP_ADMIN_TOKEN, ele usa ela.

Se não existir, ele usa o valor "trocar-esse-token-agora" (que é um token de exemplo).

Então você já pode deixar esse valor de exemplo no GitHub, sem medo, porque:

você sabe que em produção vai trocar por outro via variável de ambiente;

quem clonar o repositório só vai conseguir mexer na API local, não na sua VPS.

Se quiser, pode trocar essa string por algo mais claro, tipo:

ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "DEV-TEST-TOKEN-NAO-USAR-EM-PROD")


Esse valor vai pro GitHub, é só um token de desenvolvimento.

2. Como usar isso em uma VPS formatada (SEM editar código)

Depois que formatar a VPS e clonar o repositório de novo:

cd /root
git clone https://github.com/ColtSeals/pmesp-vps.git
cd pmesp-vps
bash app/services/setup.sh


Agora você tem duas opções:

2.1. Modo “rápido” de teste (usando token default do código)

Sem mexer em nada:

cd /root/pmesp-vps
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000


Nesse modo, o token de admin é aquele do código:

DEV-TEST-TOKEN-NAO-USAR-EM-PROD   # ou "trocar-esse-token-agora" se não trocou


Então, ao usar /docs:

Em qualquer rota de admin (ex: GET /users)

No campo X-Admin-Token você coloca exatamente esse texto.

🔐 Isso é só pra desenvolvimento / teste.

2.2. Modo “seguro” (produção) com variável de ambiente

Quando você estiver pronto pra usar sério, não precisa alterar GitHub.

Só faz na VPS:

cd /root/pmesp-vps
source venv/bin/activate

# define um token forte SÓ nessa VPS
export PMESP_ADMIN_TOKEN="UmTokenBemGrandeESecreto123!@#"

uvicorn app.main:app --host 0.0.0.0 --port 8000


Agora:

A API ignora o valor do código,

E passa a usar o valor da variável PMESP_ADMIN_TOKEN.

No /docs, em X-Admin-Token, você usa:

UmTokenBemGrandeESecreto123!@#


Se alguém olhar seu GitHub, ele só vê o token de exemplo, não o token real.

3. Se você quiser “fixar” um token só de demo no GitHub

Se a ideia é: “quero um token fixo pra usar em ambiente de teste, mesmo que eu esqueça de exportar variável” — basta trocar a string padrão em main.py:

ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "PMESP-DEMO-TOKEN-123")


Esse “PMESP-DEMO-TOKEN-123” vai pra GitHub.

Qualquer pessoa que subir essa API localmente consegue testar usando esse token.

Na sua VPS real, você sempre deve setar PMESP_ADMIN_TOKEN com outro valor, e pronto.

4. Preciso criar algum arquivo especial?

Não é obrigatório.

Opção simples (recomendada pro seu nível agora):

Não criar arquivo nenhum.

Deixar o ADMIN_TOKEN com um valor de exemplo no código.

Na VPS séria, você muda via:

export PMESP_ADMIN_TOKEN="seu-token-de-verdade"


só antes de rodar o uvicorn.

Se quiser, no próximo passo eu posso te escrever um README.md em português explicando:

como subir a API do zero (incluindo token),

quais rotas existem,

e como usar o token no /docs.

Você disse:
ok coloquei no github so pra testar  ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")


como fazer agora para poder rodar na vps zerada
O ChatGPT disse:
Pensou por dois segundos

Perfeito, agora a brincadeira começa pra valer 😄
Você já subiu o código com:

ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")


Então, numa VPS zerada, o passo a passo é esse aqui.

1. Acessar a VPS como root

Via SSH, algo tipo:

ssh root@IP_DA_SUA_VPS

2. Instalar o básico (só na primeira vez)
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip

3. Clonar seu repositório
cd /root
git clone https://github.com/ColtSeals/pmesp-vps.git
cd pmesp-vps


Se quiser conferir:

ls
# deve aparecer: app  venv (depois), requirements / setup.sh se tiver etc

4. Rodar o script de setup (cria venv e instala libs)

Deixa o script executável:

chmod +x app/services/setup.sh


Roda:

bash app/services/setup.sh


Ele vai:

criar venv/

instalar FastAPI, Uvicorn, SQLAlchemy etc.

Quando terminar, ele mesmo mostra os comandos pra subir a API.

5. Ativar o ambiente virtual

Sempre que for mexer na API:

cd /root/pmesp-vps
source venv/bin/activate


Você vai ver algo tipo (venv) no começo da linha do terminal.

6. Definir (ou não) o token de admin

Como você deixou isso no código:

ADMIN_TOKEN = os.getenv("PMESP_ADMIN_TOKEN", "trocar-esse-token-agora")


Se você não exportar nada, o token de admin será exatamente:

trocar-esse-token-agora


Se você quiser sobrescrever (produção), você roda:

export PMESP_ADMIN_TOKEN="MeuTokenSecretoQueNaoVaiProGithub!"


Pra teste, pode usar o padrão mesmo (sem exportar nada).

7. Subir a API

Ainda dentro de /root/pmesp-vps com o venv ativo:

uvicorn app.main:app --host 0.0.0.0 --port 8000


Dica: como a API chama useradd, chpasswd, chage, o ideal é rodar isso como root (você já está logado como root, então tá safe).

Deixa esse comando rodando (ele mostra logs).

8. Testar se está respondendo

Em outro SSH na mesma VPS:

cd /root/pmesp-vps
source venv/bin/activate
curl http://127.0.0.1:8000/ping


Se vier algo assim:

{"status":"ok","time":"2025-..."}


✅ API no ar.

Do seu PC, no navegador:

http://IP_DA_SUA_VPS:8000/docs

9. Usar o token nas rotas de admin

No /docs:

Rota pública (não precisa token):

GET /ping

POST /auth/check

Rotas de admin (precisam do header X-Admin-Token):

/users (todas)

/sites

/monitor/online

/tickets

etc.

Quando você clicar em uma rota protegida (ex: GET /users → Try it out), vai aparecer um campo:

X-Admin-Token

Pra teste, se você não exportou variável na VPS, coloca:

trocar-esse-token-agora


E dá Execute.

Se o token estiver errado ou vazio, a API responde:

{"detail": "Não autorizado (admin token inválido)"}


Aí você sabe que a proteção está funcionando.

Se quiser, na próxima mensagem manda:

se o /ping respondeu;

se no /docs aparece o campo X-Admin-Token nas rotas protegidas;

e se com trocar-esse-token-agora você consegue usar POST /users e POST /sites.

Aí a gente já parte pra: criar sites, criar um usuário e depois ligar isso no seu cliente Flet 😊

Extended thinking
O ChatGPT pode cometer erros. Confira informações
