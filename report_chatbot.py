import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pickle
import spacy
import os
from medical_chatbot import queryReportChatbotLLM
MONGO_USER=os.environ["MONGO_USER"]
MONGO_PASS=os.environ["MONGO_PASS"]
uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.lxnui.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
DB=client["user_report_data_db"]
COLLECTION = DB["report_data"]

redis_client = redis.StrictRedis(host=os.environ["REDIS_HOST"],port=int(os.environ["REDIS_PORT"]),password=os.environ["REDIS_PASS"],decode_responses=True)

nlp=spacy.load("en_core_web_lg")
chatbot_model=pickle.load(open("models/chatbot.pkl","rb"))
intent_map={0: 'welcome', 1: 'thank_you', 2: 'bye', 3: 'help', 4: 'about'}

def createUserData(user_id:str):
    docs=list(COLLECTION.find({"user_id":user_id}))
    if len(docs)<5:return False,len(docs)
    user_data=""
    for doc in docs: user_data+=doc["report_data"]
    key=f"report_chatbot_{user_id}"
    redis_client.setex(key,900,user_data)
    return True,key


def predictIntent(question):
    vector=[nlp(question).vector]
    predicted=chatbot_model.predict(vector)
    if intent_map[predicted[0]]!="help":
        return {"status":True,"intent":intent_map[predicted[0]]}
    return {'status':False}

def queryReportChatbot(key,question):
    data=redis_client.get(key)
    if not data:pass
    return queryReportChatbotLLM(data,question)

