import os
os.system('''
nohup uvicorn server:app --host 127.0.0.1 --port 8000  > chatbot1.log 2>&1 &
nohup uvicorn server:app --host 127.0.0.1 --port 8001  > chatbot2.log 2>&1 &
nohup uvicorn server:app --host 127.0.0.1 --port 8002  > chatbot3.log 2>&1 &
''')