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
import hashlib

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-flash-lite-latest')

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
        prompt = f"Translate the following text into {lang}. Return ONLY the translated text and nothing else:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error translating with Gemini: {e}")
        return text

def translate_batch(texts_dict, target_language):
    """
    Translates multiple texts in one prompt to save quota.
    texts_dict: { id: text_to_translate }
    returns: { id: translated_text }
    """
    if not texts_dict or target_language == 'en':
        return texts_dict
        
    language_map = {'hi': 'Hindi', 'te': 'Telugu'}
    lang = language_map.get(target_language, 'Hindi')
    
    # Prepare prompt
    # I'll use a numbered list to keep it clean
    items = []
    ids = []
    for art_id, text in texts_dict.items():
        if text:
            items.append(f"{len(items)+1}. {text}")
            ids.append(art_id)
            
    if not items: return {}
    
    try:
        combined_text = "\n".join(items)
        prompt = f"""Translate each of the numbered items below into {lang}. 
        Return ONLY the translated items, preserved in the same numbered list format. 
        Do not include any conversational text or explanation.

        Items to translate:
        {combined_text}"""
        
        response = model.generate_content(prompt)
        translated_raw = response.text.strip()
        
        # Regex to parse the numbered list
        import re
        results = {}
        # Match lines like "1. <translation>"
        matches = re.findall(r'(\d+)\.\s*(.*)', translated_raw)
        
        for m_idx, m_text in matches:
            idx = int(m_idx) - 1
            if 0 <= idx < len(ids):
                results[ids[idx]] = m_text.strip()
        
        # Fallback for missing items
        for art_id in ids:
            if art_id not in results:
                print(f"Batch translation missed {art_id}")
                results[art_id] = texts_dict[art_id]
        
        return results
    except Exception as e:
        print(f"Error in batch translate: {e}")
        return texts_dict

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

# Simple in-memory cache for related images, per process
ARTICLE_IMAGE_CACHE = {}


def get_related_image(title, category_name):
    cache_key = f"{title.strip().lower()}|{category_name.strip().lower()}"
    if cache_key in ARTICLE_IMAGE_CACHE:
        return ARTICLE_IMAGE_CACHE[cache_key]

    try:
        query_keywords = "+".join(filter(None, title.split()[:4])) or category_name
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY') or '0lgllKu97TlLE1FvJiBFayadHB-A3Pox-D0GIAn-caM'
        default_query = os.getenv('UNSPLASH_DEFAULT_QUERY', '').strip()

        combined_query = ' '.join(filter(None, [default_query, category_name, ' '.join(title.split()[:4])]))
        if not combined_query:
            combined_query = category_name or 'news'

        api_url = 'https://api.unsplash.com/photos/random'
        headers = {'Authorization': f'Client-ID {unsplash_key}'}

        last_exception = None
        for attempt in range(1, 4):
            try:
                # Use query-based random photo if possible
                resp = requests.get(
                    api_url,
                    params={'query': combined_query, 'orientation': 'landscape', 'content_filter': 'high'},
                    headers=headers,
                    timeout=6
                )
                if resp.ok:
                    data = resp.json()
                    image_url = data.get('urls', {}).get('regular')
                    if image_url:
                        ARTICLE_IMAGE_CACHE[cache_key] = image_url
                        return image_url
                else:
                    print(f'Unsplash {attempt}/3 status {resp.status_code}: {resp.text}')

            except Exception as e:
                last_exception = e
                print(f'Unsplash API fetch failed on attempt {attempt}: {e}')

        # Robust Fallback - use keyword-based URL with a unique signature
        # We can use a hash of the title to ensure the same image for the same article, but different for others.
        unique_sig = hashlib.md5(title.encode()).hexdigest()[:8]
        # Use keywords from combined_query or category
        keywords = requests.utils.quote(combined_query or category_name or 'news')
        
        # Better fallback: use a curated collection or just a keyword with a signature
        fallback_url = f'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&q=80&w=800&sig={unique_sig}'
        
        # If we want a different random photo from Unsplash for a keyword without an API key, 
        # it's harder now, but we can try to use their "featured" photos by keyword if we find a working URL.
        # Since source.unsplash.com is gone, we'll stick to a high-quality default with a signature for cache-busting
        # or VARIETY if possible.
        
        # Actually, let's use some category-specific high-quality base images
        category_bases = {
            'technology': 'photo-1485827404703-89b55fcc595e',
            'business': 'photo-1460925895917-afdab827c52f',
            'sports': 'photo-1508098682722-e99c43a406b2',
            'health': 'photo-1505751172876-fa1923c5c528',
            'entertainment': 'photo-1514525253361-bee8718a7439',
            'world': 'photo-1521295121783-8a321d551ad2'
        }
        
        base_id = category_bases.get(category_name.lower(), 'photo-1504711434969-e33886168f5c')
        fallback_url = f'https://images.unsplash.com/{base_id}?auto=format&fit=crop&q=80&w=800&sig={unique_sig}'
        
        ARTICLE_IMAGE_CACHE[cache_key] = fallback_url
        return fallback_url

    except Exception as e:
        unique_sig = hashlib.md5(title.encode()).hexdigest()[:8]
        print(f'get_related_image fallback error: {e}')
        # Category-based fallback even in error
        category_bases = {
            'technology': 'photo-1485827404703-89b55fcc595e',
            'business': 'photo-1460925895917-afdab827c52f',
            'sports': 'photo-1508098682722-e99c43a406b2',
            'health': 'photo-1505751172876-fa1923c5c528',
            'entertainment': 'photo-1514525253361-bee8718a7439',
            'world': 'photo-1521295121783-8a321d551ad2'
        }
        base_id = category_bases.get(category_name.lower(), 'photo-1504711434969-e33886168f5c')
        return f'https://images.unsplash.com/{base_id}?auto=format&fit=crop&q=80&w=800&sig={unique_sig}'

    except Exception as e:
        print(f'get_related_image fallback: {e}')
        return 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&q=80&w=800'

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
                
                # Use a high-quality Unsplash image as primary (per user request)
                image_url = get_related_image(title, category_name)
                
                # Check if Unsplash gave us a generic placeholder and we can find something better in HTML
                # But usually Unsplash is better quality.
                # If we don't have an image_url yet (unlikely with our fallbacks), try extraction
                if not image_url:
                    image_url = extract_image_url(description_html)
                    
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

