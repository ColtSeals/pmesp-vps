#!/bin/bash
# ==================================================================
#  PMESP MANAGER ULTIMATE V8.1 - CORREÇÃO NUMÉRICA & API
# ==================================================================

# --- ARQUIVOS DE DADOS ---
DB_PMESP="/etc/pmesp_users.json"
DB_CHAMADOS="/etc/pmesp_tickets.json"
CONFIG_SMTP="/etc/msmtprc"
LOG_MONITOR="/var/log/pmesp_monitor.log"

# Garante arquivos básicos
if [ ! -f "$DB_PMESP" ]; then
    touch "$DB_PMESP"
    chmod 666 "$DB_PMESP"
    echo "" > "$DB_PMESP"
fi

if [ ! -f "$DB_CHAMADOS" ]; then
    touch "$DB_CHAMADOS"
    chmod 666 "$DB_CHAMADOS"
fi

if [ ! -f "$LOG_MONITOR" ]; then
    touch "$LOG_MONITOR"
    chmod 644 "$LOG_MONITOR"
fi

# --- CORES ---
R="$(printf '\033[1;31m')" # Vermelho
G="$(printf '\033[1;32m')" # Verde
Y="$(printf '\033[1;33m')" # Amarelo
B="$(printf '\033[1;34m')" # Azul
P="$(printf '\033[1;35m')" # Roxo
C="$(printf '\033[1;36m')" # Ciano
W="$(printf '\033[1;37m')" # Branco
NC="$(printf '\033[0m')"  # Reset
LINE_H="${C}═${NC}"

# --- FUNÇÕES VISUAIS ---

cabecalho() {
    clear
    _tuser=$(jq '.usuario' "$DB_PMESP" 2>/dev/null | wc -l)
    _ons=$(who | grep -v 'root' | wc -l)
    _ip=$(wget -qO- ipv4.icanhazip.com 2>/dev/null || echo "N/A")

    echo -e "${C}╭${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C}╮${NC}"
    echo -e "${C}┃${P}           PMESP MANAGER V8.1 - TÁTICO INTEGRADO           ${C}┃${NC}"
    echo -e "${C}┣${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
    echo -e "${C}┃ ${Y}TOTAL USUÁRIOS: ${W}$_tuser ${Y}| ONLINE AGORA: ${G}$_ons ${Y}| IP: ${G}$_ip${C}   ┃${NC}"
    echo -e "${C}┗${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
}

barra() { echo -e "${C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# --------------------------------------------------------------------------
# --- FUNÇÕES DE BACKEND ---
# --------------------------------------------------------------------------

# --- INSTALAÇÃO DE DEPENDÊNCIAS ---
install_deps() {
    cabecalho
    echo -e "${Y}Instalando Dependências Básicas...${NC}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y >/dev/null 2>&1
    apt-get install -y bc screen nano net-tools lsof cron zip unzip jq msmtp msmtp-mta ca-certificates >/dev/null 2>&1
    echo -e "${G}Sistema Pronto! Pacotes básicos instalados.${NC}"
    sleep 2
}

# --- CONFIGURAÇÃO DO GMAIL (SMTP) ---
configurar_smtp() {
    cabecalho
    echo -e "${P}>>> CONFIGURAÇÃO DE SERVIDOR DE E-MAIL (GMAIL)${NC}"
    echo "Necessário ter a 'Senha de App' gerada no Google."
    echo ""

    read -p "Seu E-mail Gmail (Ex: pmesp@gmail.com): " email_adm
    read -p "Sua Senha de App (16 letras): " senha_app

    echo -e "\n${Y}Configurando o cliente SMTP...${NC}"

    cat <<EOF > "$CONFIG_SMTP"
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        /var/log/msmtp.log

account        gmail
host           smtp.gmail.com
port           587
from           $email_adm
user           $email_adm
password       $senha_app

account default : gmail
EOF

    chmod 600 "$CONFIG_SMTP"

    echo -e "${G}Configuração salva em $CONFIG_SMTP!${NC}"
    echo -e "Enviando e-mail de teste..."

    echo -e "Subject: Teste PMESP Manager\n\nO sistema de e-mail da VPS esta operante." | msmtp "$email_adm"

    if [ $? -eq 0 ]; then
        echo -e "${G}E-mail de teste enviado! Verifique sua caixa de entrada.${NC}"
    else
        echo -e "${R}Erro ao enviar. Verifique se a senha de app está correta.${NC}"
    fi
    read -p "Enter para voltar..."
}

# --- GESTÃO DE USUÁRIOS (CRIAR - CORRIGIDO) ---
criar_usuario() {
    cabecalho
    echo -e "${G}>>> NOVO CADASTRO DE USUÁRIO${NC}"
    read -p "Matrícula (RE): " matricula
    read -p "Email do Policial: " email
    read -p "Login (Usuário): " usuario

    # Verifica se já existe no Linux
    if id "$usuario" >/dev/null 2>&1; then
        echo -e "\n${R}ERRO: Usuário Linux '$usuario' já existe!${NC}"
        sleep 2
        return
    fi

    read -p "Senha Provisória: " senha
    read -p "Validade (Dias): " dias
    read -p "Limite de Telas (Sessões): " limite

    echo -e "\n${Y}Criando usuário no sistema...${NC}"

    # --- CORREÇÃO AQUI: Adicionado --badname para aceitar números ---
    useradd -M -s /bin/false --badname "$usuario"

    # Verifica se o comando useradd funcionou
    if [ $? -ne 0 ]; then
        echo -e "${R}FALHA CRÍTICA: O Linux recusou criar o usuário '$usuario'.${NC}"
        echo "Verifique os logs ou tente um nome começando com letra."
        read -p "Enter para voltar..."
        return
    fi

    # Define a senha
    echo "$usuario:$senha" | chpasswd
    if [ $? -ne 0 ]; then
         echo -e "${R}Erro ao definir senha.${NC}"
         userdel -f "$usuario" # Remove o usuário quebrado
         return
    fi

    # Validade do Linux
    data_final=$(date -d "+$dias days" +"%Y-%m-%d")
    chage -E "$data_final" "$usuario"

    # Registra no JSON apenas se tudo deu certo
    jq -n \
        --arg u "$usuario" \
        --arg s "$senha" \
        --arg d "$dias" \
        --arg l "$limite" \
        --arg m "$matricula" \
        --arg e "$email" \
        --arg h "PENDENTE" \
        '{usuario: $u, senha: $s, dias: $d, limite: $l, matricula: $m, email: $e, hwid: $h}' \
        >> "$DB_PMESP"

    echo -e "${G}SUCESSO! Usuário '$usuario' criado e registrado.${NC}"
    read -p "Enter..."
}

# --- VINCULAR HWID ---
atualizar_hwid() {
    cabecalho
    echo -e "${Y}>>> VINCULAR HWID${NC}"
    read -p "Usuário alvo: " user_alvo
    read -p "Novo HWID: " novo_hwid

    if ! grep -q "\"usuario\": \"$user_alvo\"" "$DB_PMESP"; then
        echo -e "${R}Usuário não encontrado!${NC}"
        sleep 2
        return
    fi

    # Pega dados antigos
    linha=$(grep "\"usuario\": \"$user_alvo\"" "$DB_PMESP")
    s=$(echo "$linha" | jq -r .senha)
    d=$(echo "$linha" | jq -r .dias)
    l=$(echo "$linha" | jq -r .limite)
    m=$(echo "$linha" | jq -r .matricula)
    e=$(echo "$linha" | jq -r .email)

    # Remove linha antiga
    grep -v "\"usuario\": \"$user_alvo\"" "$DB_PMESP" > "${DB_PMESP}.tmp" && mv "${DB_PMESP}.tmp" "$DB_PMESP"

    # Adiciona nova com HWID
    jq -n \
        --arg u "$user_alvo" \
        --arg s "$s" \
        --arg d "$d" \
        --arg l "$l" \
        --arg m "$m" \
        --arg e "$e" \
        --arg h "$novo_hwid" \
        '{usuario: $u, senha: $s, dias: $d, limite: $l, matricula: $m, email: $e, hwid: $h}' \
        >> "$DB_PMESP"

    echo -e "${G}HWID Atualizado.${NC}"
    sleep 2
}

# --- LISTAR USUÁRIOS ---
listar_usuarios() {
    cabecalho
    echo -e "${C}>>> LISTA DE USUÁRIOS CADASTRADOS${NC}"
    barra
    echo -e "${W}%-15s | %-10s | %-5s | %-5s | %s${NC}" "USUÁRIO" "MATRÍCULA" "DIAS" "LIM" "HWID"
    barra

    if [ -s "$DB_PMESP" ]; then
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            usuario=$(echo "$line" | jq -r '.usuario // empty' 2>/dev/null)
            [ -z "$usuario" ] && continue
            [ "$usuario" = "null" ] && continue

            matricula=$(echo "$line" | jq -r '.matricula // "-"')
            dias=$(echo "$line" | jq -r '.dias // "-"')
            limite=$(echo "$line" | jq -r '.limite // "-"')
            hwid=$(echo "$line" | jq -r '.hwid // "-"')
            hwid_short="${hwid:0:15}..."

            printf "${Y}%-15s${NC} | %-10s | %-5s | %-5s | %s\n" \
                "$usuario" "$matricula" "$dias" "$limite" "$hwid_short"
        done < <(jq -c '.' "$DB_PMESP" 2>/dev/null)
    else
        echo -e "${Y}Nenhum usuário cadastrado.${NC}"
    fi
    echo ""
    read -p "Enter para voltar..."
}

# --- REMOVER USUÁRIO ---
remover_usuario_direto() {
    cabecalho
    echo -e "${R}>>> REMOVER USUÁRIO${NC}"
    read -p "Digite o LOGIN do usuário: " user_alvo

    if ! id "$user_alvo" >/dev/null 2>&1 || ! grep -q "\"usuario\": \"$user_alvo\"" "$DB_PMESP"; then
        echo -e "${R}ERRO: Usuário não existe.${NC}"
        sleep 2
        return
    fi

    read -p "Tem certeza? (s/N): " confirmacao
    if [[ "$confirmacao" =~ ^[Ss]$ ]]; then
        userdel -f "$user_alvo" >/dev/null 2>&1
        grep -v "\"usuario\": \"$user_alvo\"" "$DB_PMESP" > "${DB_PMESP}.tmp" && mv "${DB_PMESP}.tmp" "$DB_PMESP"
        echo -e "${G}Usuário removido.${NC}"
    else
        echo -e "${Y}Cancelado.${NC}"
    fi
    sleep 2
}

# --- ALTERAR VALIDADE ---
alterar_validade_direto() {
    cabecalho
    echo -e "${Y}>>> ALTERAR VALIDADE (RENOVAÇÃO)${NC}"
    read -p "Digite o LOGIN do usuário: " user_alvo

    if ! grep -q "\"usuario\": \"$user_alvo\"" "$DB_PMESP"; then
        echo -e "${R}ERRO: Usuário não encontrado.${NC}"
        sleep 2
        return
    fi

    read -p "Nova validade (dias a partir de hoje): " novos_dias
    if ! [[ "$novos_dias" =~ ^[0-9]+$ ]]; then
        echo -e "${R}Inválido.${NC}"
        sleep 2
        return
    fi

    nova_data=$(date -d "+$novos_dias days" +"%Y-%m-%d")
    chage -E "$nova_data" "$user_alvo"

    # Atualiza JSON
    linha=$(grep "\"usuario\": \"$user_alvo\"" "$DB_PMESP")
    grep -v "\"usuario\": \"$user_alvo\"" "$DB_PMESP" > "${DB_PMESP}.tmp" && mv "${DB_PMESP}.tmp" "$DB_PMESP"

    # Reconstrói objeto com dias atualizados
    # (Simplificado: mantem outros dados e só troca dias)
    echo "$linha" | jq --arg d "$novos_dias" '.dias = $d' >> "$DB_PMESP"

    echo -e "${G}Renovado para $novos_dias dias (até $nova_data).${NC}"
    sleep 2
}

# --- USUÁRIOS VENCIDOS ---
usuarios_vencidos() {
    cabecalho
    echo -e "${R}>>> USUÁRIOS EXPIRADOS OU PRÓXIMOS (7 DIAS)${NC}"
    barra
    echo -e "${W}%-15s | %-12s | %s${NC}" "USUÁRIO" "DATA EXPIRAÇÃO" "STATUS"
    barra

    if [ -s "$DB_PMESP" ]; then
        today=$(date +%s)
        seven_days=$((today + 60*60*24*7))

        while IFS= read -r line; do
            [ -z "$line" ] && continue
            usuario=$(echo "$line" | jq -r '.usuario // empty' 2>/dev/null)
            [ -z "$usuario" ] && continue

            expire_raw=$(chage -l "$usuario" 2>/dev/null | grep 'Account expires' | awk -F ': ' '{print $2}')
            [ "$expire_raw" = "never" ] && continue
            
            expire_sec=$(date -d "$expire_raw" +%s 2>/dev/null)
            [ -z "$expire_sec" ] && continue

            if [ "$expire_sec" -lt "$today" ]; then
                printf "%-15s | %-12s | ${R}%s${NC}\n" "$usuario" "$expire_raw" "EXPIRADO"
            elif [ "$expire_sec" -lt "$seven_days" ]; then
                printf "%-15s | %-12s | ${Y}%s${NC}\n" "$usuario" "$expire_raw" "PRÓXIMO"
            fi
        done < <(jq -c '.' "$DB_PMESP" 2>/dev/null)
    else
        echo -e "${Y}Vazio.${NC}"
    fi
    echo ""
    read -p "Enter..."
}

# --- MONITORAMENTO ONLINE ---
mostrar_usuarios_online() {
    tput civis
    trap 'tput cnorm; clear; return' SIGINT
    clear
    echo -e "${R}Pressione CTRL + C para voltar.${NC}"
    sleep 1

    while true; do
        cabecalho
        echo -e "${C}>>> MONITORAMENTO REAL-TIME ${Y}(Atualiza 2s)${NC}"
        barra
        printf "${W}%-15s | %-8s | %-6s${NC}\n" "Usuário" "Sessões" "Limite"
        barra

        active=0
        if [ -s "$DB_PMESP" ]; then
            jq -c 'unique_by(.usuario)[]' "$DB_PMESP" 2>/dev/null | while read -r line; do
                user=$(echo "$line" | jq -r '.usuario')
                limite=$(echo "$line" | jq -r '.limite // 0')
                sessoes=$(who | awk -v u="$user" '$1==u {c++} END {print c+0}')

                if [ "$sessoes" -gt 0 ]; then
                    active=$((active + 1))
                    printf "${Y}%-15s${NC} | %-8s | %-6s\n" "$user" "$sessoes" "$limite"
                fi
            done
        fi

        [ "$active" -eq 0 ] && echo -e "${Y}Ninguém online.${NC}"

        sleep 2
        tput cuu $((active + 6))
        tput ed
    done
}

# --- RESETAR SENHA ---
recuperar_senha() {
    cabecalho
    echo -e "${P}>>> RESETAR SENHA${NC}"
    [ ! -f "$CONFIG_SMTP" ] && { echo -e "${R}Configure SMTP antes!${NC}"; sleep 2; return; }

    read -p "Usuário: " user_alvo
    if ! grep -q "\"usuario\": \"$user_alvo\"" "$DB_PMESP"; then
        echo -e "${R}Usuário não existe.${NC}"; sleep 2; return
    fi

    linha=$(grep "\"usuario\": \"$user_alvo\"" "$DB_PMESP")
    email=$(echo "$linha" | jq -r .email)
    [ -z "$email" ] || [ "$email" == "null" ] && { echo -e "${R}Sem e-mail cadastrado.${NC}"; sleep 2; return; }

    nova_senha=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 8)
    echo "$user_alvo:$nova_senha" | chpasswd

    # Atualiza JSON
    grep -v "\"usuario\": \"$user_alvo\"" "$DB_PMESP" > "${DB_PMESP}.tmp" && mv "${DB_PMESP}.tmp" "$DB_PMESP"
    echo "$linha" | jq --arg s "$nova_senha" '.senha = $s' >> "$DB_PMESP"

    echo -e "Enviando para ${Y}$email${NC}..."
    (
        echo "To: $email"
        echo "Subject: [PMESP] Nova Senha"
        echo -e "\nNova Senha: $nova_senha"
    ) | msmtp "$email"

    [ $? -eq 0 ] && echo -e "${G}Enviado!${NC}" || echo -e "${R}Erro no envio. Senha: $nova_senha${NC}"
    read -p "Enter..."
}

# --- CHAMADOS ---
novo_chamado() {
    cabecalho
    ID=$((1000 + RANDOM % 8999))
    DATA=$(date "+%d/%m/%Y %H:%M")
    read -p "Usuário: " user
    read -p "Problema: " prob

    jq -n --arg i "$ID" --arg u "$user" --arg p "$prob" --arg s "ABERTO" --arg d "$DATA" \
        '{id: $i, usuario: $u, problema: $p, status: $s, data: $d}' >> "$DB_CHAMADOS"
    echo -e "${G}Chamado #$ID aberto.${NC}"; sleep 2
}

gerenciar_chamados() {
    while true; do
        cabecalho
        echo -e "${C}>>> CHAMADOS${NC}"
        printf "${B}%-6s | %-10s | %-10s | %-15s${NC}\n" "ID" "USER" "STATUS" "DESC"
        barra
        while read -r l; do
            [ -z "$l" ] && continue
            i=$(echo "$l" | jq -r .id)
            u=$(echo "$l" | jq -r .usuario)
            s=$(echo "$l" | jq -r .status)
            p=$(echo "$l" | jq -r .problema)
            cor=$([ "$s" == "ABERTO" ] && echo "$R" || echo "$G")
            printf "%-6s | %-10s | ${cor}%-10s${NC} | %-15s\n" "$i" "$u" "$s" "${p:0:15}..."
        done < "$DB_CHAMADOS"

        echo -e "\n[1] Fechar | [2] Deletar | [0] Voltar"
        read -p "Op: " opc
        case $opc in
            1)
                read -p "ID: " id
                tmp=$(mktemp)
                while read -r l; do
                    cid=$(echo "$l" | jq -r .id)
                    [ "$cid" == "$id" ] && l=$(echo "$l" | jq '.status="ENCERRADO"')
                    echo "$l" >> "$tmp"
                done < "$DB_CHAMADOS"
                mv "$tmp" "$DB_CHAMADOS"
                ;;
            2)
                read -p "ID: " id
                grep -v "\"id\": \"$id\"" "$DB_CHAMADOS" > t.json && mv t.json "$DB_CHAMADOS"
                ;;
            0) return ;;
        esac
    done
}

# --- INSTALAR SQUID (PORTA SECRETA 40000) ---
install_squid() {
    cabecalho
    echo -e "${C}>>> SQUID PROXY (PORTA 40000)${NC}"
    apt-get update -y >/dev/null 2>&1
    apt-get install -y squid >/dev/null 2>&1

    [ -f /etc/squid/squid.conf ] && cp /etc/squid/squid.conf "/etc/squid/squid.conf.bak"

    cat <<EOF >/etc/squid/squid.conf
# PORTA ALTA (BLINDADA)
http_port 40000

acl all src 0.0.0.0/0
http_access allow all

# Ocultar headers (Anti-Sniffer)
request_header_access Via deny all
request_header_access X-Forwarded-For deny all
EOF

    systemctl enable squid >/dev/null 2>&1
    systemctl restart squid
    echo -e "${G}SQUID rodando na porta 40000!${NC}"
    echo "Libere a porta 40000 no Firewall."
    read -p "Enter..."
}

# --- INSTALAR SSLH (PORTA SECRETA 50000) ---
install_sslh() {
    cabecalho
    echo -e "${P}>>> SSLH (PORTA 50000)${NC}"
    apt-get install -y sslh >/dev/null 2>&1

    cat <<'EOF' >/etc/default/sslh
RUN=yes
DAEMON_OPTS="--user sslh --listen 0.0.0.0:443 --ssh 127.0.0.1:22 --pidfile /run/sslh/sslh.pid"
EOF

    systemctl enable sslh >/dev/null 2>&1
    systemctl restart sslh
    echo -e "${G}SSLH rodando na porta 443!${NC}"
    echo "Configure o APP/Injector para conectar em: 443"
    read -p "Enter..."
}

# --- CRON MONITOR ---
monitorar_acessos() {
    while read -r line; do
        user=$(echo "$line" | jq -r '.usuario' 2>/dev/null)
        [ -z "$user" ] || [ "$user" == "null" ] && continue
        limite=$(echo "$line" | jq -r '.limite')
        sessoes=$(who | awk -v u="$user" '$1==u {c++} END {print c+0}')

        if [ "$sessoes" -gt 0 ]; then
            echo "$(date '+%F %T') | $user | $sessoes/$limite" >> "$LOG_MONITOR"
            # Derrubar se exceder (Opcional - Descomente abaixo)
            # [ "$limite" -gt 0 ] && [ "$sessoes" -gt "$limite" ] && pkill -KILL -u "$user"
        fi
    done < "$DB_PMESP"
}

configurar_cron_monitor() {
    cabecalho
    script_path=$(readlink -f "$0")
    echo "Criando CRON para monitoramento..."
    (crontab -l 2>/dev/null | grep -v "--cron-monitor"; echo "*/1 * * * * /bin/bash $script_path --cron-monitor >/dev/null 2>&1") | crontab -
    echo -e "${G}Monitoramento Ativado.${NC}"
    sleep 2
}

# --- MENU PRINCIPAL ---
menu() {
    while true; do
        cabecalho
        echo -e "${C}╭${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C}╮${NC}"
        echo -e "${C}┃${W}          ${G}🛡️ GESTÃO BLINDADA PMESP V8.1 ${NC}                  ${C}┃${NC}"
        echo -e "${C}┣${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
        
        echo -e "${C}┃ ${W}${G}01${W} ⮞ CRIAR USUÁRIO ${C}                                     ┃${NC}"
        echo -e "${C}┃ ${W}${G}02${W} ⮞ LISTAR USUÁRIOS ${C}                                   ┃${NC}"
        echo -e "${C}┃ ${W}${G}03${W} ⮞ REMOVER USUÁRIO ${C}                                   ┃${NC}"
        echo -e "${C}┃ ${W}${G}04${W} ⮞ RENOVAR DIAS ${C}                                      ┃${NC}"
        echo -e "${C}┃ ${W}${G}05${W} ⮞ VER VENCIDOS ${C}                                      ┃${NC}"
        echo -e "${C}┃ ${W}${G}06${W} ⮞ MONITOR ONLINE ${C}                                    ┃${NC}"
        echo -e "${C}┃ ${W}${G}07${W} ⮞ RESETAR SENHA ${C}                                     ┃${NC}"
        echo -e "${C}┃ ${W}${G}08${W} ⮞ VINCULAR HWID ${C}                                     ┃${NC}"
        echo -e "${C}┣${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
        echo -e "${C}┃ ${W}${G}09${W} ⮞ ABRIR CHAMADO ${C}                                     ┃${NC}"
        echo -e "${C}┃ ${W}${G}10${W} ⮞ GERIR CHAMADOS ${C}                                    ┃${NC}"
        echo -e "${C}┃ ${W}${G}11${W} ⮞ CONFIG SMTP (GMAIL) ${C}                               ┃${NC}"
        echo -e "${C}┣${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
        echo -e "${C}┃ ${W}${G}12${W} ⮞ INSTALAR DEPENDÊNCIAS ${C}                             ┃${NC}"
        echo -e "${C}┃ ${W}${G}13${W} ⮞ INSTALAR SQUID (Porta 40000) ${C}                      ┃${NC}"
        echo -e "${C}┃ ${W}${G}14${W} ⮞ INSTALAR SSLH (Porta 443) ${C}                       ┃${NC}"
        echo -e "${C}┃ ${W}${G}15${W} ⮞ ATIVAR MONITOR (CRON) ${C}                             ┃${NC}"
        echo -e "${C}┣${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
        echo -e "${C}┃ ${R}00${W} ⮞ SAIR ${C}                                                ┃${NC}"
        echo -e "${C}┗${LINE_H}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"

        read -p "${W}➤ OPÇÃO:${NC} " op
        case $op in
            1|01) criar_usuario ;;
            2|02) listar_usuarios ;;
            3|03) remover_usuario_direto ;;
            4|04) alterar_validade_direto ;;
            5|05) usuarios_vencidos ;;
            6|06) mostrar_usuarios_online ;;
            7|07) recuperar_senha ;;
            8|08) atualizar_hwid ;;
            9|09) novo_chamado ;;
            10) gerenciar_chamados ;;
            11) configurar_smtp ;;
            12) install_deps ;;
            13) install_squid ;;
            14) install_sslh ;;
            15) configurar_cron_monitor ;;
            0|00) exit 0 ;;
            *) echo -e "${R}Opção inválida.${NC}"; sleep 1 ;;
        esac
    done
}

if [ "$1" == "--cron-monitor" ]; then
    monitorar_acessos
    exit 0
fi

menu
