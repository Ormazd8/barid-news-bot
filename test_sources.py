from rss_fetcher import fetch_recent_news, deduplicate
from config import RSS_SOURCES

print(f"تعداد منابع: {len(RSS_SOURCES)}")
print("=" * 50)

news = fetch_recent_news()
print(f"بعد از جمع‌آوری: {len(news)} خبر")
print("=" * 50)

sources = {}
for item in news:
    src = item.get("source", "?")
    sources[src] = sources.get(src, 0) + 1

print("خبر از هر منبع:")
for src, count in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {count:3d} - {src}")

print("=" * 50)

news2 = deduplicate(news)
print(f"بعد از حذف تکراری: {len(news2)} خبر")
print(f"حذف شده: {len(news) - len(news2)}")
