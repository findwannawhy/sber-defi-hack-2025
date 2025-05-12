# Используем официальный образ Python (обновлено до 3.11)
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY . .

# Открываем порт, на котором будет работать uvicorn
EXPOSE 8000

# Команда для запуска приложения (будет переопределена в docker-compose.yaml)
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
# Оставляем CMD закомментированным или удаляем, т.к. command указан в docker-compose.yaml 
