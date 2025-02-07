from dotenv import load_dotenv
load_dotenv()
from fastapi import Request,FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.output_parsers import JsonOutputParser
import json,random,uvicorn
from medical_chatbot import queryMedicalChatbot
from report_chatbot import createUserData,predictIntent,queryReportChatbot


parser=JsonOutputParser()
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

irrelavant_question_error=[
    "I apologize, but I'm unable to respond to questions that aren't related to medical topics.",
    "Sorry, but I can only answer questions that pertain to medical matters.",
    "I regret to inform you that I can't answer questions outside the medical field.",
    "Unfortunately, I'm not able to address inquiries that are unrelated to medicine.",
    "I'm sorry, but my expertise is limited to medical-related questions only.",
    "Regrettably, I can't provide answers to questions that don't involve medical issues.",
    "I appreciate your understanding, but I can only engage with medical inquiries.",
    "Sorry, I'm unable to help with questions that are not connected to medical topics.",
    "I'm afraid I can't assist with anything that isn't related to medical matters.",
    "Unfortunately, I can only provide information on medical-related questions."
]
response_map=json.load(open("response_map.json"))

@app.post("/query")
async def answer_query(request:Request):
    data=await request.json()
    question=data['queryResult']["queryText"]
    response=queryMedicalChatbot(question)
    try:
        data=eval(response)
    except:
        try:
            data=parser.parse(response)
        except:
            return JSONResponse({
                'fulfillmentText':"Ooops!! I think i am tired. Please try again.."
            })

    if data['status']=="true":
        return JSONResponse(
            {
            'fulfillmentText':data['ans'],
            },
            status_code=200
            )
    elif data["status"]=="absent":
        return JSONResponse(
            {
            'fulfillmentText':"Oops!! I dont have this information in my knoledge base. Please try something else..",
            },
            status_code=200
            )
    else:
        return JSONResponse(
            {
            'fulfillmentText':irrelavant_question_error[random.randint(0,9)],
            },
            status_code=200
            )

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
    resp=predictIntent(question)
    if resp["status"]:return JSONResponse({"data":response_map[resp["intent"]][random.randint(0,9)]},status_code=200)
    resp=queryReportChatbot(key,question)
    try:
        data=parser.parse(resp)
    except:
        try:
            data=eval(resp)
        except:
            JSONResponse({"data":"Error retreiving data.."},status_code=200)
    if data["status"]=="true":
        return JSONResponse({"data":data["ans"]},status_code=200)
    return JSONResponse({"data":"It seems the information relevant to your question doesnt exist..."},status_code=400)


if __name__=="__main__":
    print("Server Running on port 6000")
    uvicorn.run("server:app",host="localhost",port=6000,reload=True)