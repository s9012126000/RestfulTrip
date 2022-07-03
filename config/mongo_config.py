from pymongo import MongoClient
from dotenv import load_dotenv
import os


load_dotenv()
client = MongoClient(
    f"{os.getenv('mongo_host')}:27017",
    username=os.getenv('mongo_user'),
    password=os.getenv('mongo_password'),
    authMechanism=os.getenv('mongo_authMechanism')
    )
