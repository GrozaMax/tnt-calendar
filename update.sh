#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

echo "[INFO]  Обновление tnt-calendar (ветка: $BRANCH)..."
git pull origin "$BRANCH"
# docker compose build --quiet
docker compose build
docker compose up -d
echo "[OK]    Готово. Данные (БД, загрузки) сохранены в volume app_data."
docker compose ps
