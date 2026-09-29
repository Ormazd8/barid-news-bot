import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

_ai_keys_str = os.environ.get("AI_API_KEYS", "")
AI_API_KEYS = [k.strip() for k in _ai_keys_str.split(",") if k.strip()]

AI_API_URL = "https://api.groq.com/openai/v1/chat/completions"
AI_MODEL = "openai/gpt-oss-20b"

HOURS_WINDOW = 6

RSS_SOURCES = [
    "https://www.anthropic.com/news/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://news.ycombinator.com/rss",
    "https://www.jiqizhixin.com/rss",
    "https://blog.google/technology/ai/rss/",
    "https://ai.meta.com/blog/rss/",
    "https://mistral.ai/news/feed.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "http://export.arxiv.org/rss/cs.AI",
    "https://www.qbitai.com/feed",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/LocalLLaMA/.rss",
]