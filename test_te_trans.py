import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

from news.models import Article
from news.utils import translate_text

text = "Hello, welcome to our news app!"
trans = translate_text(text, 'te')
print(f"Original: {text}")
print(f"Telugu: {trans}")
