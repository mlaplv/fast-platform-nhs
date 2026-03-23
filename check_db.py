import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartShop.settings')
django.setup()

from admins.models.news import News

slugs = [
    'chinh-sach-bao-mat',
    'dieu-khoan-su-dung',
    'chinh-sach-doi-tra',
    'huong-dan-mua-hang'
]

for slug in slugs:
    try:
        news = News.objects.get(slug=slug)
        print(f"--- Slug: {slug} ---")
        print(f"ID: {news.id}")
        print(f"Title: {news.title}")
        print(f"Status: {news.status}")
        print(f"Content length: {len(str(news.content)) if news.content else 0}")
        print(f"Content Data length: {len(str(news.content_data)) if news.content_data else 0}")
        print(f"Content preview: {str(news.content)[:100]}...")
    except News.DoesNotExist:
        print(f"--- Slug: {slug} NOT FOUND ---")
    except Exception as e:
        print(f"--- Slug: {slug} ERROR: {e} ---")
