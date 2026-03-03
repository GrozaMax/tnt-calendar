#!/bin/bash
# Скрипт деплоя на VPS (запускается автоматически через GitHub Actions)
# Можно также запустить вручную: ssh user@host 'bash ~/tnt-calendar/scripts/deploy.sh'

set -e

APP_DIR=~/tnt-calendar

echo "📦 Обновляем код..."
cd $APP_DIR
git pull origin main

echo "🐳 Пересобираем и запускаем контейнеры..."
docker compose build --no-cache
docker compose up -d

echo "🔍 Статус контейнеров:"
docker compose ps

echo "✅ Деплой завершён!"
