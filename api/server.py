from dotenv import load_dotenv
load_dotenv()
from fastapi import Request,FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random,uvicorn
from medical_chatbot import queryMedicalChatBotLLM
from report_chatbot import createUserData,queryReportChatbot
from utils import validateToken
# from utils import Configs


app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query")
async def answer_query(request:Request):        
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"mssg":"No token provided"},status_code=401)
    token = auth_header.split(" ")[1]
    user_id=validateToken(token)
    if user_id==None: return JSONResponse({"mssg":"Session expired..Login again"},status_code=401)
    data=await request.json()
    question=data["question"]
    response=queryMedicalChatBotLLM(question,user_id)
    return JSONResponse({"response":response},status_code=200)

@app.get("/test")
async def test():
    return {"data":"ok"}


@app.get("/create_agent/{user_id}")
async def create_agent(user_id:str):
    status,key=createUserData(str(user_id))
    if status:return JSONResponse({"mssg":"Agent Created","key":key},status_code=201)
    return JSONResponse({"mssg":f"Not enough data for creating age.You need minimum 5 reports, You have {key} reports"},status_code=400)

@app.post("/chat")
async def chat(request:Request):
    data=await request.json()
    key,question=data["key"],data["question"]
    # resp=predictIntent(question)
    # if resp["status"]:return JSONResponse({"data":Configs.response_map[resp["intent"]][random.randint(0,9)]},status_code=200)
    resp=queryReportChatbot(key,question)
    if resp:
        return JSONResponse({"resp":resp},status_code=200)
    return JSONResponse({"resp":None,"mssg":"Agent Expired"},status_code=400)


# if __name__=="__main__":
#     print("Server Running on port 6000")
#     uvicorn.run("server:app",host="127.0.0.1",port=8000,reload=True)

# from mangum import Mangum
# handler = Mangum(app)