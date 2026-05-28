from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv('GEMINI_API_KEY'),
        temperature=0.3
    )
    print("Testing ChatGoogleGenerativeAI with gemini-2.5-flash...")
    response = llm.invoke("Say hello in one word.")
    print(f"Success! Response: {response.content}")
except Exception as e:
    print(f"Failed: {e}")


