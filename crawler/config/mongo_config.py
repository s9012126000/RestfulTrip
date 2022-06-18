from pymongo import MongoClient
from dotenv import load_dotenv
import os


load_dotenv()
client = MongoClient(
    f"{os.getenv('host')}:27017",
    username=os.getenv('mongouser'),
    password=os.getenv('password'),
    authMechanism=os.getenv('authMechanism')
    )