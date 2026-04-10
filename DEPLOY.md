# Деплой на Oracle Cloud (и аналогичные VPS)

Telegram-бот + веб-панель (FastAPI). Два контейнера из одного Docker-образа, общий volume для SQLite и загрузок.

## 1. Создание VM в Oracle Cloud

1. **Compute -> Instances -> Create instance** в консоли OCI.
2. Образ: **Canonical Ubuntu** (рекомендуется) или Oracle Linux.
3. Форма: **VM.Standard.A1.Flex** (ARM, Always Free) или совместимая x86.
4. SSH-ключ: сгенерируйте или загрузите свой.
5. **Virtual Cloud Network -> Subnet -> Security List -> Ingress Rules** — добавьте правило:
   - Source CIDR: `0.0.0.0/0`, Protocol: TCP, Destination Port: **8000**.

## 2. Установка и запуск

Подключитесь по SSH и выполните:

```bash
git clone https://github.com/GrozaMax/tnt-calendar.git
cd tnt-calendar
bash setup.sh
```

Скрипт `setup.sh` сделает всё автоматически:
- Установит Docker (если не стоит)
- Спросит **TELEGRAM_BOT_TOKEN** и **ADMIN_TELEGRAM_IDS** (ваш Telegram ID)
- Сгенерирует случайный **WEB_LOGIN_SECRET** (пароль для входа в веб)
- Создаст `.env` с Docker-путями
- Откроет порт 8000 в iptables (Oracle Linux/Ubuntu блокируют его по умолчанию)
- Соберёт образ и запустит `docker compose up -d`

В конце скрипт выведет ссылку на веб-панель и сгенерированный пароль — **сохраните его**.

## 3. Проверка

```bash
docker compose ps          # оба контейнера running
docker compose logs -f bot # логи бота (Ctrl+C для выхода)
```

- Веб-панель: `http://<PUBLIC_IP>:8000`
- Бот должен отвечать в Telegram.

## 4. Обновление версии (после мержа новых фич)

Рабочий цикл:

1. Разрабатываете локально на своей ветке (например `otladka`).
2. Мержите в `master` на GitHub (PR или `git merge` + `git push`).
3. На сервере по SSH:

```bash
cd tnt-calendar
bash update.sh            # тянет текущую ветку (обычно master)
# или явно:
bash update.sh master
```

Скрипт делает `git pull origin <ветка>`, пересобирает образ и перезапускает контейнеры. Даунтайм — несколько секунд на рестарт.

Данные (БД и загрузки) хранятся в Docker volume `app_data` и не теряются при обновлении.

## 5. Nginx и HTTPS (опционально)

1. Установите **nginx** и **certbot** на хосте (не в контейнере).
2. Проксируйте `https://your-domain` -> `127.0.0.1:8000`.
3. В Ingress Rules VCN откройте порт **443**, закройте прямой доступ к **8000**.

## 6. PostgreSQL (опционально)

Для production можно заменить SQLite на Postgres: задайте `DATABASE_URL=postgresql+asyncpg://...` в `.env`. Каталог `UPLOADS_DIR` по-прежнему нужен на общем volume.
