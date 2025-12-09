from pymongo import MongoClient
import os

mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(mongodb_url)
db = client["task_tracker"]

def get_db():
    return db
