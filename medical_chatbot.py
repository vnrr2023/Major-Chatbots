import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI,HarmBlockThreshold, HarmCategory
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.chains import  create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
import redis
import json
from threading import Thread

redis_client = redis.StrictRedis(host=os.environ["REDIS_HOST"],port=int(os.environ["REDIS_PORT"]),password=os.environ["REDIS_PASS"],decode_responses=True)
llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0,api_key=os.environ["GOOGLE_API_KEY"],
                            safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    })
gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.environ["GOOGLE_API_KEY"])
persist_directory = "chatbot_db"
collection_name="medical_data"
vector_store=Chroma(persist_directory=persist_directory,collection_name=collection_name, embedding_function=gemini_embeddings)
retriever = vector_store.as_retriever()

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", '''Your name is ArogyaGpt.You are tasked with answering questions based on the provided medical context, which includes information about home remedies, symptoms, risk factors, and prevention methods for a specific disease.
Strictly **avoid** suggesting medicines, chemicals, supplements, or any form of pharmaceutical treatment. Your response should focus only on natural remedies, symptoms, and preventive measures as mentioned in the context.  
provide A brief answer to the question, around 40 to 50 words, starting with context related to the question.
If the question asked is not relevant to the context or if it not related to medical or not present in the context just say: Ooops Try some another Gpt for this question.
Ensure your response is concise and friendly, without any preamble or extra text.
'''),
    ("human", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])
history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain) 

def saveHistoryToRedis(user_id,question:str,ai_resp:str,user_history:list):
    ttl = redis_client.ttl(f"arogya_bot_{user_id}")
    ttl = ttl if ttl > 0 else 1200
    new_data=[{'role': 'human', 'content': question},{'role': 'ai','content': ai_resp}]
    user_history.extend(new_data)
    redis_client.setex("arogya_bot_"+str(user_id), ttl, json.dumps(user_history))
    

def queryMedicalChatBotLLM(question,user_id):
    user_history=redis_client.get("arogya_bot_"+str(user_id))
    user_history=json.loads(user_history) if user_history else []
    print(user_history)
    ai_resp=rag_chain.invoke({
        "input": question,
        "chat_history":user_history
    })['answer']
    Thread(target=saveHistoryToRedis,args=(user_id,question,ai_resp,user_history)).start()
    return ai_resp

def queryReportChatbotLLM(data,question):
    messages = [
        ("system",f"""
        You are task is to answer questions based on the context only.Give me the reponse in json format only with two keys
        "ans": the answer in short about 60 to 70 words based on the context only. paraphrase the question while answering
        "status": value should be "true" if the answer is found in the context else will be "false".
        give me the response in json format with no preamble and no nested json and only text.
        Respond with a single-line JSON object without any extra formatting, indentation, or backticks.
        Dont give ```json\\n at start also
         Context: {data}
        """),
        ("human",question)
        ]
    ai_msg = llm.invoke(messages)
    return ai_msg.content