# Используем официальный образ Node.js (выберите подходящую версию, например LTS - Long Term Support)
FROM node:20-alpine

# Устанавливаем pnpm глобально
RUN npm install -g pnpm

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и pnpm-lock.yaml (если используется)
COPY package.json pnpm-lock.yaml* ./
# Если pnpm-lock.yaml не используется, удалите его из строки выше

# Устанавливаем зависимости
RUN pnpm install --frozen-lockfile

# Копируем остальной код приложения
COPY . .

# Открываем порт для dev сервера
EXPOSE 5173

# Команда для запуска (будет переопределена в docker-compose.yaml)
# CMD ["pnpm", "run", "dev"]
# Оставляем CMD закомментированным или удаляем, т.к. command указан в docker-compose.yaml 