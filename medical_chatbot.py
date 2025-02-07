import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

template='''
You are tasked with answering questions based on the provided medical context, which includes information about home remedies, symptoms, risk factors, and prevention methods for a specific disease.
Strictly **avoid** suggesting medicines, chemicals, supplements, or any form of pharmaceutical treatment. Your response should focus only on natural remedies, symptoms, and preventive measures as mentioned in the context.  
Please return the answer in JSON format with the following two keys:
ans: A brief answer to the question, around 40 to 50 words, starting with context related to the question.
status: This should be "true" if the answer is present in the context;if you dont find an ans in the context then it should be "absent";otherwise if the question is not revelant to medical then it  should be "false."
Ensure your response is concise and friendly, without any preamble or extra text.
Respond with a single-line JSON object without any extra formatting, indentation, or backticks.
Dont give ```json\\n at start also
<context>{context} <context>
Question: {input}
'''

llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0,api_key=os.environ["GOOGLE_API_KEY"])
gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.environ["GOOGLE_API_KEY"])
persist_directory = "chatbot_db"
collection_name="medical_data"
vector_store=Chroma(persist_directory=persist_directory,collection_name=collection_name, embedding_function=gemini_embeddings)
retriever = vector_store.as_retriever()
prompt=ChatPromptTemplate.from_template(template)
document_chain=create_stuff_documents_chain(llm,prompt)
retrieval_chain=create_retrieval_chain(retriever,document_chain)
   
def queryMedicalChatbot(question):
    response=retrieval_chain.invoke({"input":question})['answer']
    return response
    
def queryLLM(prompt,data):
    messages = [("system",prompt),("human",data)]
    ai_msg = llm.invoke(messages)
    return ai_msg.content

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