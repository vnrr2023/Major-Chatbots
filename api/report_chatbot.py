import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# from motor.motor_asyncio import AsyncIOMotorClient

import os
from medical_chatbot import queryReportChatbotLLM
MONGO_USER=os.environ["MONGO_USER"]
MONGO_PASS=os.environ["MONGO_PASS"]
uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.lxnui.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
# client = AsyncIOMotorClient(uri)

    
DB=client["user_report_data_db"]
COLLECTION = DB["report_data"]

redis_client = redis.StrictRedis(host=os.environ["REDIS_HOST"],port=int(os.environ["REDIS_PORT"]),password=os.environ["REDIS_PASS"],decode_responses=True)


def createUserData(user_id:str):
    docs=list(COLLECTION.find({"user_id":user_id}))
    if len(docs)<5:return False,len(docs)
    user_data=""
    for doc in docs: user_data+=doc["report_data"]
    key=f"report_chatbot_{user_id}"
    redis_client.setex(key,900,user_data)
    print(user_data)
    return True,key


def queryReportChatbot(key,question):
    data=redis_client.get(key)
    if not data:return None
    return queryReportChatbotLLM(data,question)

