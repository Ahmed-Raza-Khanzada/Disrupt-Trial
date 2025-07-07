import os
import google.generativeai as genai
from langchain.chat_models import ChatOpenAI
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] =os.getenv("OPENAI_API_KEY" , "")



my_gemini_api = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=my_gemini_api)




def get_engine(priority=0):


    if priority==0:
        print("Gemini Loaded")
        llm = genai.GenerativeModel(model_name='gemini-2.5-pro')
    else:
        print("Open AI Loaded")
        llm= ChatOpenAI(
            model = "gpt-4",
            temperature=0.0,
            max_tokens=1000,
            timeout=None,
            max_retries=2
        )


    return llm