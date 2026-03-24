import os
import django
import google.generativeai as genai
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

text = "Hello"
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

try:
    response = model.generate_content(f"Translate '{text}' into Telugu. Return ONLY the translated text.")
    print(f"Original: {text}")
    print(f"Telugu: {response.text}")
except Exception as e:
    print(f"Error for Telugu: {e}")
