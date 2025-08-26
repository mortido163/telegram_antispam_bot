FROM postgres:15-alpine

# Установка дополнительных инструментов
RUN apk add --no-cache \
    curl \
    wget \
    nano \
    less \
    bash

# Установка дополнительных PostgreSQL инструментов
RUN apk add --no-cache postgresql-client

# Создание рабочей директории
WORKDIR /tools

# Копирование полезных скриптов
COPY scripts/db-tools/ /tools/

# Установка переменных окружения
ENV PGHOST=postgres
ENV PGPORT=5432
ENV PGUSER=postgres
ENV PGDATABASE=telegram_bot

CMD ["tail", "-f", "/dev/null"]
