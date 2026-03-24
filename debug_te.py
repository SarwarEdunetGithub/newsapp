import os
import django
import google.generativeai as genai
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

from news.models import Article
from news.utils import translate_text

text = "Hello"
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-lite-latest')

try:
    prompt = f"Translate '{text}' into Telugu. Return ONLY the translated text."
    response = model.generate_content(prompt)
    print(f"Original: {text}")
    print(f"Telugu: {response.text}")
except Exception as e:
    print(f"Error for Telugu: {e}")
