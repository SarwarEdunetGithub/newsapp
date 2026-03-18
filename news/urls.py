from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet)
router.register(r'categories', views.CategoryViewSet)

urlpatterns = [
    # Frontend Pages
    path('', views.index, name='index'),
    
    # APIs
    path('api/', include(router.urls)),
    path('api/trending/', views.TrendingNewsView.as_view(), name='trending_news'),
    path('api/translate/<int:pk>/<str:lang>/', views.TranslateArticleView.as_view(), name='translate_article'),
    path('api/force-fetch/', views.ForceFetchView.as_view(), name='force_fetch'),
]
