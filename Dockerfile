# Используем официальный образ Python
FROM python:3.12-slim

# Установим системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Создаем непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Открываем порт (если нужен для мониторинга)
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "src/main.py"]
