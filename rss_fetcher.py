import feedparser
import hashlib
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from config import RSS_SOURCES, HOURS_WINDOW


def fetch_recent_news():
    """جمع‌آوری اخبار ۶ ساعت اخیر از تمام منابع"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    all_news = []

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                published = _get_published(entry)
                if published and published >= cutoff:
                    all_news.append({
                        "title": entry.get("title", "").strip(),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500],
                        "source": feed.feed.get("title", url),
                        "published": published,
                    })
        except Exception as e:
            print(f"[RSS ERROR] {url} -> {e}")

    return all_news


def _get_published(entry):
    """استخراج زمان انتشار"""
    for key in ("published", "updated"):
        if key in entry:
            try:
                dt = date_parser.parse(entry[key])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return None


def deduplicate(news_list):
    """حذف تکراری‌ها بر اساس شباهت عنوان (SimHash ساده)"""
    seen = []
    unique = []

    for item in news_list:
        h = _simhash(item["title"])
        if any(_hamming(h, s) < 5 for s in seen):
            continue
        seen.append(h)
        unique.append(item)

    return unique


def _simhash(text):
    """هش ۶۴ بیتی ساده بر اساس کلمات"""
    words = text.lower().split()
    v = [0] * 64
    for w in words:
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        for i in range(64):
            v[i] += 1 if (h >> i) & 1 else -1
    result = 0
    for i in range(64):
        if v[i] > 0:
            result |= (1 << i)
    return result


def _hamming(a, b):
    return bin(a ^ b).count("1")