import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content("Hello, are you working?")
print(response.text)
