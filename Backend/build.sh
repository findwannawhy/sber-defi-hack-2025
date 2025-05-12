#!/bin/bash
# Выход при ошибке
set -e

echo ">>> Установка системных зависимостей..."
apt-get update && apt-get install -y libomp-dev

echo ">>> Инициализация сабмодулей..."
# Убедимся, что git установлен (обычно он есть, но на всякий случай)
apt-get install -y git
# Инициализация и обновление сабмодулей
git submodule update --init --recursive

echo ">>> Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo ">>> Запуск установки smartbugs..."
# Проверяем наличие директории и скрипта перед запуском
if [ -d "smartbugs" ] && [ -f "smartbugs/install/setup-venv.sh" ]; then
  echo "Найдена директория smartbugs и скрипт setup-venv.sh."
  cd smartbugs
  # Даем права на выполнение скрипту
  chmod +x install/setup-venv.sh
  # Запускаем скрипт
  bash install/setup-venv.sh
  cd ..
  echo "Установка smartbugs завершена."
else
  echo "ПРЕДУПРЕЖДЕНИЕ: Директория '''smartbugs''' или скрипт '''smartbugs/install/setup-venv.sh''' не найдены. Пропуск установки."
fi

echo ">>> Сборка завершена!" 