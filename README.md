# Task Tracker

### Функции
- Создание пользователей, проектов, задач (через Swagger)
- Фильтры по статусу, приоритету, исполнителю
- Сводка «Загрузка по проектам»
- Сводка «Задачи пользователя»

### Как запустить

# 1. Клонируем репозиторий на компьютер

# 2. Создаём виртуальное окружение
- cd ArtPar_NW_CP2025/
- python -m venv venv
- source venv/bin/activate

# 3. Устанавливаем зависимости
- pip install -r backend/requirements.txt

# 4. Запускаем MongoDB (если не установлен — через Docker)
- sudo docker run -d --name mongo-tt -p 27017:27017 mongo:latest
# или просто запустите локальный mongod
- sudo systemctl start mongod

# 5. Запускаем сервер
- cd backend
- uvicorn main:app --reload

# 6. Запускаем сайт (в отдельной консоли)
- cd frontend
- python3 -m http.server 8080
