from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .models import Article, Category
from .serializers import ArticleSerializer, CategorySerializer
from .utils import translate_text, fetch_and_save_news, translate_batch
import threading

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        date = self.request.query_params.get('date')
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(description__icontains=search)
        if date:
            # expected format YYYY-MM-DD
            queryset = queryset.filter(published_date__date=date)
        
        return queryset

class TrendingNewsView(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        # Taking top 10 most recent trending articles, fallback to overall latest 10
        trending = Article.objects.filter(is_trending=True).order_by('-published_date')[:10]
        if not trending:
            return Article.objects.all().order_by('-published_date')[:10]
        return trending

class BatchTranslateView(APIView):
    def post(self, request, lang):
        article_ids = request.data.get('ids', [])
        if not article_ids:
            return Response({"error": "No IDs provided"}, status=400)
            
        articles = Article.objects.filter(id__in=article_ids)
        
        # Prepare batch for titles and summaries
        batch = {}
        for a in articles:
            batch[f"{a.id}_title"] = a.title
            batch[f"{a.id}_summary"] = a.summary or a.description
            
        translated_batch = translate_batch(batch, lang)
        
        results = {}
        for a in articles:
            results[str(a.id)] = {
                "title": translated_batch.get(f"{a.id}_title", a.title),
                "summary": translated_batch.get(f"{a.id}_summary", a.summary or a.description)
            }
            
        return Response(results)

class TranslateArticleView(APIView):
    def get(self, request, pk, lang):
        try:
            article = Article.objects.get(pk=pk)
            # Use gemini to translate
            title_trans = translate_text(article.title, lang)
            sum_trans = translate_text(article.summary, lang)
            return Response({
                "title": title_trans,
                "summary": sum_trans,
                "language": lang
            })
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=404)

class ForceFetchView(APIView):
    def post(self, request):
        Article.objects.all().delete()
        fetch_and_save_news()
        return Response({"status": "News fetched successfully and database refreshed!"})

def index(request):
    return render(request, 'news/index.html')
