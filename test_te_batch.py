import os
import django
import google.generativeai as genai
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

from news.utils import translate_batch

batch = {
    "1": "Hello world",
    "2": "How are you?",
    "3": "I love news"
}

results = translate_batch(batch, 'te')
print("Batch Translation (Telugu):")
for k, v in results.items():
    print(f"{k}: {v}")
