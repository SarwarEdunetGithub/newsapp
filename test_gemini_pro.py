import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

try:
    response = model.generate_content("Say hello in Hindi")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
