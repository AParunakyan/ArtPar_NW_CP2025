from pymongo import MongoClient
import os

#получение URL подключения к MongoDB из переменной окружения или использование по умолчанию
mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")

#создание клиента MongoDB
client = MongoClient(mongodb_url)
#подключение к базе данных
db = client["task_tracker"]

def get_db():
    #функция-зависимость для FastAPI — возвращает объект базы данных
    return db
