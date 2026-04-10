# Образ для сервисов bot и web (два контейнера из одного Dockerfile, разные command в compose)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Данные на volume (создаётся при первом сохранении картинки / init_db)
RUN mkdir -p /app/data/uploads

EXPOSE 8000

# По умолчанию — бот; в docker-compose для web переопределяется command
CMD ["python", "main.py"]
