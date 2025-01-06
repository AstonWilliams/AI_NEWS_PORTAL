from django.db import models

class RSSFeed(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField()
    published = models.DateTimeField()
    summary = models.TextField()
    approx_traffic = models.CharField(max_length=255, blank=True, null=True)
    picture = models.URLField(blank=True, null=True)
    picture_source = models.URLField(blank=True, null=True)
    news_item_titles = models.TextField(blank=True, null=True)
    news_item_urls = models.TextField(blank=True, null=True)
    news_item_pictures = models.TextField(blank=True, null=True)
    news_item_sources = models.TextField(blank=True, null=True)
    used = models.BooleanField(default=False)  # New field to track if the entry has been used

    def __str__(self):
        return self.title

class BlogArticle(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
