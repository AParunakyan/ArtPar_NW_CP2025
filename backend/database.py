from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["task_tracker"]

def get_db():
    try:
        client.admin.command("ping")
        return db
    except Exception:
        raise ConnectionError("Не удалось подключиться к MongoDB. Запустите mongod!")
