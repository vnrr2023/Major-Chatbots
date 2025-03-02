import datetime
import jwt
import os
import json
from langchain_core.output_parsers import JsonOutputParser
SECRET_KEY = os.environ["SECRET_KEY"]

def validateToken(token):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
        return str(payload["user_id"])
    except:
        return None
    
# class Configs:
#     parser=JsonOutputParser()
#     irrelavant_question_error=[
#     "I apologize, but I'm unable to respond to questions that aren't related to medical topics.",
#     "Sorry, but I can only answer questions that pertain to medical matters.",
#     "I regret to inform you that I can't answer questions outside the medical field.",
#     "Unfortunately, I'm not able to address inquiries that are unrelated to medicine.",
#     "I'm sorry, but my expertise is limited to medical-related questions only.",
#     "Regrettably, I can't provide answers to questions that don't involve medical issues.",
#     "I appreciate your understanding, but I can only engage with medical inquiries.",
#     "Sorry, I'm unable to help with questions that are not connected to medical topics.",
#     "I'm afraid I can't assist with anything that isn't related to medical matters.",
#     "Unfortunately, I can only provide information on medical-related questions."
#     ]
    # response_map=json.load(open("response_map.json"))