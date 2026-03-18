import os
import requests
import feedparser
import re
import google.generativeai as genai
from .models import Article, Category
from datetime import datetime
from django.utils import timezone
from dateutil import parser
import traceback

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_article(content):
    if not content:
        return ""
    try:
        prompt = f"Summarize the following news article into a clear, concise paragraph of 2-3 sentences highlighting the main points:\n\n{content}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error summarizing with Gemini: {e}")
        return content[:200] + "..." if len(content) > 200 else content

def translate_text(text, target_language):
    if not text or target_language == 'en':
        return text
    
    language_map = {'hi': 'Hindi', 'te': 'Telugu'}
    lang = language_map.get(target_language)
    if not lang: return text

    try:
        prompt = f"Translate the following text into {lang}:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error translating with Gemini: {e}")
        return text

def extract_image_url(html_content):
    match = re.search(r'<img[^>]+src="([^">]+)"', html_content)
    if match: return match.group(1)
    return ""

def rewrite_article(title, description):
    if not description or len(description) < 20:
        return description
    try:
        prompt = f"""Rewrite the following news article based on the title and description provided. 
        Create a detailed, engaging, and professional news report of 2-3 paragraphs. 
        Ensure it is completely original, avoids plagiarism, and sounds like a professional journalist wrote it.
        
        Title: {title}
        Original Context: {description}
        
        Return ONLY the rewritten article content."""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error rewriting with Gemini: {e}")
        return description

def get_related_image(title, category_name):
    try:
        # Create a more specific query from the title
        # Use first 3 words of title for search variety
        keywords = " ".join(title.split()[:4])
        import hashlib
        seed = hashlib.md5(title.encode()).hexdigest()[:8]
        # Query Unsplash with title keywords for better relevance
        url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&q=80&w=800&q=news,{category_name.lower()},{keywords.replace(' ', ',')}&sig={seed}"
        return url
    except:
        return f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&q=80&w=800"

def fetch_and_save_news():
    # Modern Google News RSS topics
    categories = ['TECHNOLOGY', 'BUSINESS', 'SPORTS', 'HEALTH', 'ENTERTAINMENT', 'WORLD']
    
    for category_name in categories:
        cat_obj, created = Category.objects.get_or_create(
            name=category_name.capitalize(),
            slug=category_name.lower()
        )
        
        url = f"https://news.google.com/rss/headlines/section/topic/{category_name}?hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(url)
            
            for item in feed.entries[:5]: # Limit to 5 per category to save Gemini credits/time
                title = item.get('title')
                link = item.get('link')
                published_at = item.get('published')
                
                if not title or not link or not published_at:
                    continue
                    
                if Article.objects.filter(original_url=link).exists():
                    continue  
                    
                description_html = item.get('summary', '')
                clean_desc = re.sub(r'<[^>]+>', '', description_html).strip()
                
                source_name = "News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source_name = parts[1]

                # Use Gemini for clean summary and rewritten full content
                summary = summarize_article(clean_desc)
                rewritten_content = rewrite_article(title, clean_desc)
                
                # Get a highly related image
                image_url = extract_image_url(description_html)
                if not image_url:
                    image_url = get_related_image(title, category_name)
                    
                try:
                    pub_date = parser.parse(published_at)
                except:
                    pub_date = timezone.now()
                    
                Article.objects.create(
                    title=title,
                    description=clean_desc,
                    content=rewritten_content,
                    summary=summary,
                    source=source_name,
                    author="",
                    category=cat_obj,
                    published_date=pub_date,
                    image_url=image_url,
                    original_url=link,
                    is_trending=True if category_name == 'WORLD' else False
                )
        except Exception as e:
            print(f"Failed to fetch {category_name}: {e}")
            traceback.print_exc()

