from django.urls import path
from . import views

urlpatterns = [
    path('scrape-rss-feed/', views.scrape_rss_feed, name='scrape_rss_feed'),
    path('generate-blog-post/<int:feed_id>/', views.generate_blog_post, name='generate_blog_post'),
    path('render-blog-post/<int:article_id>/', views.render_blog_post, name='render_blog_post'),
    path('', views.home, name='home'),
    path('load-articles/', views.load_articles, name='load_articles'),
]
