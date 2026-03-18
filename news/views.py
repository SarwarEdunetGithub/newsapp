from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .models import Article, Category
from .serializers import ArticleSerializer, CategorySerializer
from .utils import translate_text, fetch_and_save_news
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
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(description__icontains=search)
            
        return queryset

class TrendingNewsView(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        # Taking top 5 most recent if is_trending, or just top 5 overall if none checked
        trending = Article.objects.filter(is_trending=True)[:5]
        if not trending:
            return Article.objects.all()[:5]
        return trending

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
