import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

from news.models import Article
from news.utils import translate_text

a = Article.objects.all().first()
if a:
    print(f"Article ID: {a.id}")
    print(f"Original Title: {a.title}")
    trans = translate_text(a.title, 'hi')
    print(f"Translated Title (Hindi): {trans}")
else:
    print("No articles found!")
