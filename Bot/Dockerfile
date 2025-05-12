# Используем официальный образ Python (обновлено до 3.11)
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем системные зависимости, необходимые для сборки asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
# Используем --no-cache-dir для уменьшения размера слоя
RUN pip install --no-cache-dir -r requirements.txt

# Удаляем системные зависимости, которые больше не нужны (опционально, но рекомендуется для уменьшения образа)
# Если другие пакеты потребуют их во время выполнения, этот шаг нужно будет убрать или изменить.
# RUN apt-get purge -y --auto-remove build-essential libpq-dev

# Копируем остальной код приложения
COPY . .

EXPOSE 8080


# Команда для запуска приложения (будет переопределена в docker-compose.yaml)
# CMD ["python", "bot.py"]
# Оставляем CMD закомментированным или удаляем, т.к. command указан в docker-compose.yaml 