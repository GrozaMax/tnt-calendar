#!/usr/bin/env bash
set -euo pipefail

# ─── Цвета ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*" >&2; }

# ─── 1. Проверка / установка Docker ─────────────────────────────────
install_docker() {
    info "Docker не найден. Устанавливаю..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
    else
        err "Не удалось определить ОС. Установите Docker вручную: https://docs.docker.com/engine/install/"
        exit 1
    fi

    case "$ID" in
        ubuntu|debian)
            sudo apt-get update -qq
            sudo apt-get install -y -qq ca-certificates curl >/dev/null
            sudo install -m 0755 -d /etc/apt/keyrings
            sudo curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
            sudo chmod a+r /etc/apt/keyrings/docker.asc
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$ID $(. /etc/os-release && echo "${VERSION_CODENAME:-$VERSION}") stable" \
                | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update -qq
            sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
            ;;
        ol|rhel|centos|fedora|almalinux|rocky)
            sudo dnf -y install dnf-plugins-core >/dev/null 2>&1 || true
            sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null \
                || sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo 2>/dev/null
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
            sudo systemctl enable --now docker
            ;;
        *)
            err "Автоустановка Docker не поддержана для $ID. Установите вручную."
            exit 1
            ;;
    esac

    sudo usermod -aG docker "$USER" 2>/dev/null || true
    ok "Docker установлен"
}

if ! command -v docker &>/dev/null; then
    install_docker
else
    ok "Docker уже установлен: $(docker --version)"
fi

if ! docker compose version &>/dev/null; then
    err "docker compose plugin не найден. Установите: https://docs.docker.com/compose/install/"
    exit 1
fi

# ─── 2. Директория проекта ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f docker-compose.yml ]; then
    err "Запустите скрипт из корня репозитория tnt-calendar (docker-compose.yml не найден)"
    exit 1
fi
ok "Директория проекта: $SCRIPT_DIR"

# ─── 3. Формирование .env ───────────────────────────────────────────
if [ -f .env ]; then
    warn ".env уже существует."
    read -rp "Перезаписать? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        info "Оставляю текущий .env без изменений"
        SKIP_ENV=true
    else
        SKIP_ENV=false
    fi
else
    SKIP_ENV=false
fi

if [ "$SKIP_ENV" = false ]; then
    echo ""
    info "Нужно заполнить два обязательных параметра."
    echo ""

    read -rp "  TELEGRAM_BOT_TOKEN (от @BotFather): " BOT_TOKEN
    while [ -z "$BOT_TOKEN" ]; do
        warn "Токен не может быть пустым"
        read -rp "  TELEGRAM_BOT_TOKEN: " BOT_TOKEN
    done

    read -rp "  ADMIN_TELEGRAM_IDS (ваш Telegram ID, можно несколько через запятую): " ADMIN_IDS
    while [ -z "$ADMIN_IDS" ]; do
        warn "ID не может быть пустым"
        read -rp "  ADMIN_TELEGRAM_IDS: " ADMIN_IDS
    done

    WEB_SECRET=$(openssl rand -hex 32)
    ok "WEB_LOGIN_SECRET сгенерирован автоматически"

    cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
DATABASE_URL=sqlite+aiosqlite:////app/data/crossfit_hub.db
ADMIN_TELEGRAM_IDS=$ADMIN_IDS
WEB_LOGIN_SECRET=$WEB_SECRET
WEB_DEBUG=false
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_SECRET_KEY=$(openssl rand -hex 32)
UPLOADS_DIR=/app/data/uploads
LOG_LEVEL=INFO
EOF

    ok ".env создан"
fi

# ─── 4. Открытие порта 8000 (iptables — Oracle Cloud) ───────────────
open_port() {
    local port=$1
    if sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
        ok "Порт $port уже открыт в iptables"
        return
    fi
    info "Открываю порт $port в iptables..."
    sudo iptables -I INPUT 1 -p tcp --dport "$port" -j ACCEPT

    if command -v netfilter-persistent &>/dev/null; then
        sudo netfilter-persistent save 2>/dev/null || true
    elif [ -f /etc/sysconfig/iptables ]; then
        sudo sh -c 'iptables-save > /etc/sysconfig/iptables'
    else
        sudo sh -c 'iptables-save > /etc/iptables/rules.v4' 2>/dev/null || true
    fi
    ok "Порт $port открыт и сохранён"
}

open_port 8000

# ─── 5. Сборка и запуск ─────────────────────────────────────────────
info "Собираю Docker-образ..."
docker compose build --quiet

info "Запускаю контейнеры..."
docker compose up -d

# ─── 6. Итог ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Деплой завершён!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

PUBLIC_IP=$(curl -s --connect-timeout 3 ifconfig.me 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "<ваш_IP>")
echo -e "  Веб-панель:  ${CYAN}http://${PUBLIC_IP}:8000${NC}"
echo -e "  Бот:         работает в фоне"
echo ""

if [ "$SKIP_ENV" = false ]; then
    echo -e "  ${YELLOW}Запомните WEB_LOGIN_SECRET (пароль для входа в веб):${NC}"
    echo -e "  ${CYAN}$WEB_SECRET${NC}"
    echo ""
fi

echo "  Полезные команды:"
echo "    docker compose ps          — статус контейнеров"
echo "    docker compose logs -f bot — логи бота"
echo "    docker compose logs -f web — логи веб-панели"
echo "    bash update.sh             — обновить до новой версии"
echo ""
echo -e "  ${YELLOW}Не забудьте открыть порт 8000 в Ingress Rules вашего VCN (Oracle Cloud Console).${NC}"
echo ""
