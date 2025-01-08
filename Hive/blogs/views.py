import re
import requests
import xml.etree.ElementTree as ET
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import RSSFeed, BlogArticle
from meta_ai_api import MetaAI

def scrape_rss_feed():
    print("Starting RSS feed scraping...")
    rss_feed_url = "https://trends.google.com/trending/rss?geo=GB"
    response = requests.get(rss_feed_url)
    if response.status_code != 200:
        print("Failed to fetch RSS feed. Status code:", response.status_code)
        return

    root = ET.fromstring(response.content)
    for item in root.findall(".//item"):
        title = item.findtext("title", default="N/A")
        link = item.findtext("link", default="N/A")
        pub_date = item.findtext("pubDate", default="N/A")
        approx_traffic = item.findtext("{https://trends.google.com/trending/rss}approx_traffic", default="N/A")
        description = item.findtext("description", default="N/A")
        picture = item.findtext("{https://trends.google.com/trending/rss}picture", default="N/A")
        picture_source = item.findtext("{https://trends.google.com/trending/rss}picture_source", default="N/A")

        news_item_titles = []
        news_item_urls = []
        news_item_pictures = []
        news_item_sources = []

        for news_item in item.findall("{https://trends.google.com/trending/rss}news_item"):
            news_item_titles.append(news_item.findtext("{https://trends.google.com/trending/rss}news_item_title", default="N/A"))
            news_item_urls.append(news_item.findtext("{https://trends.google.com/trending/rss}news_item_url", default="N/A"))
            news_item_pictures.append(news_item.findtext("{https://trends.google.com/trending/rss}news_item_picture", default="N/A"))
            news_item_sources.append(news_item.findtext("{https://trends.google.com/trending/rss}news_item_source", default="N/A"))

        # Convert the pub_date to the required format
        try:
            pub_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError as e:
            print("Date conversion error:", e)
            pub_date = timezone.now()

        # Logging the scraped data
        print(f"Scraped RSS Feed: Title={title}, Link={link}, Published={pub_date}, Summary={description}")

        RSSFeed.objects.create(
            title=title,
            link=link,
            published=pub_date,
            summary=description,
            approx_traffic=approx_traffic,
            picture=picture,
            picture_source=picture_source,
            news_item_titles="; ".join(news_item_titles),
            news_item_urls="; ".join(news_item_urls),
            news_item_pictures="; ".join(news_item_pictures),
            news_item_sources="; ".join(news_item_sources),
            used=False  # Mark new RSS entries as not used
        )
        print("RSS feed entry saved:", title)

def generate_blog_post(feed):
    topic = feed.title
    news_item_urls = feed.news_item_urls.split("; ")
    news_item_sources = feed.news_item_sources.split("; ")

    print("Generating blog post for topic:", topic)

    # Generate the prompt for the AI with the required details
    prompt_message = (
        f"""Generate a engaging professional and informal and appropriate tone crafted informational yet engaging blog post 
        with rich professional markdown formatting italics,quotes,links to sources,embeded images from unsplash,etc using ,use words with encoded urls and follow
        the following structure and given information:\n"""
        f"Title: {topic}\n"
        "Introduction: Introductory paragraph on the topic\n"
        "Discussion: Detailed discussion on the topic\n"
        "Final Note: A concluding note\n"
        "Conclusion: A summary of the topic\n"
        f"Sources(INCLUDE WORDS having embedded links): {', '.join(news_item_urls)}\n"
        "Please use the included urls for more information on writing the article"
    )

    # Logging the request data being sent to the AI
    print("Request data being sent to AI:", prompt_message)

    ai = MetaAI()
    response = ai.prompt(message=prompt_message)
    
    # Logging the AI's response data
    print("Response from AI:", response)

    blog_post_content = response.get('message', '')
    sources = response.get('sources', [])

    # Extract sections using regular expressions
    introduction = re.search(r'Introduction\n(.*?)\nDiscussion', blog_post_content, re.DOTALL)
    discussion = re.search(r'Discussion\n(.*?)\nFinal Note', blog_post_content, re.DOTALL)
    final_note = re.search(r'Final Note\n(.*?)\nConclusion', blog_post_content, re.DOTALL)
    conclusion = re.search(r'Conclusion\n(.*?)\nSources', blog_post_content, re.DOTALL)

    introduction = introduction.group(1).strip() if introduction else "No introduction provided."
    discussion = discussion.group(1).strip() if discussion else "No discussion provided."
    final_note = final_note.group(1).strip() if final_note else "No final note provided."
    conclusion = conclusion.group(1).strip() if conclusion else "No conclusion provided."

    sources_str = "; ".join(news_item_sources)

    content = (
        f"{topic}\n"
        f"Introduction\n{introduction}\n\n"
        f"Discussion\n{discussion}\n\n"
        f"Final Note\n{final_note}\n\n"
        f"Conclusion\n{conclusion}\n\n"
        f"Sources\n{sources_str}"
    )

    # Save the generated article to the database
    BlogArticle.objects.create(
        title=topic,
        content=content,
        image_url=''  # Assuming there's no image URL provided
    )
    print("Blog post generated and saved:", topic)

    # Mark the RSS feed as used
    feed.used = True
    feed.save()


def refresh_data():
    print("Refreshing data...")

    # Scrape RSS feeds
    scrape_rss_feed()

    # Generate blog posts for the latest 5 unused RSS feed entries
    rss_feeds = RSSFeed.objects.filter(used=False).order_by('-published')[:1]
    for feed in rss_feeds:
        generate_blog_post(feed)

def home(request):
    last_fetch_time = request.session.get('last_fetch_time')
    current_time = timezone.now()

    if not last_fetch_time or current_time - datetime.fromisoformat(last_fetch_time) >= timedelta(minutes=1):
        refresh_data()
        request.session['last_fetch_time'] = current_time.isoformat()
        print(f"Data refreshed at: {current_time}")
    else:
        print("Using cached data from database...")

    articles = BlogArticle.objects.order_by('-created_at')[:3]
    return render(request, 'root.html', {'articles': articles})

def load_articles(request):
    # Load the latest 8 blog articles from the database
    articles = BlogArticle.objects.order_by('-created_at')[:3]
    data = {
        "articles": [
            {"id": article.id, "title": article.title, "content": article.content, "image_url": article.image_url}
            for article in articles
        ]
    }
    print("Loading articles...")
    return JsonResponse(data)

from django.shortcuts import render, get_object_or_404
from .models import BlogArticle

import urllib.parse

import urllib.parse
from django.shortcuts import render, get_object_or_404
from .models import BlogArticle

def render_blog_post(request, article_id):
    article = get_object_or_404(BlogArticle, id=article_id)
    encoded_url = urllib.parse.quote_plus(request.build_absolute_uri())
    
    context = {
        'blog_post': article,
        'url': encoded_url,
        'text': '',  # Removing text for WhatsApp link
        'title': article.title,
    }
    return render(request, 'blog.html', context)
