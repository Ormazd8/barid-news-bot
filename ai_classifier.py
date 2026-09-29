import json
import re
import requests
from config import AI_API_KEYS, AI_API_URL, AI_MODEL

CATEGORIES = [
    "\U0001F6E0 AI جدید",
    "\U0001F9E0 Research مهم",
    "\U0001F4BB Coding / Agent",
    "\U0001F3E2 ai خبر مهم شرکت‌های",
]

VALID_CATS = ["TOOL", "RESEARCH", "CODING", "COMPANY"]

PROMPT_TEMPLATE = """You are a strict AI news editor for a Persian Telegram channel.

Your goal is to publish only genuinely useful, factual, and recent AI news.
Do not accept every AI-related item.

For each news item, follow these steps:

STEP 1 - VERIFY RELEVANCE AND FACTS:
- Use only the information provided in the news item.
- Do not invent facts, dates, capabilities, prices, model names, or availability.
- A headline alone is not enough to confirm details not present in the item.
- If the item lacks enough information to produce an accurate summary, reject it.
- Do not treat old product pages or previously announced products as new releases.

STEP 2 - REMOVE DUPLICATES:
- Identify items about the same event or announcement.
- Keep only the item with the clearest and most informative source.
- Mark all other items about that event as DUPLICATE.
- Do not mark separate developments about the same company as duplicates.

STEP 3 - FILTER NEWS QUALITY:
Reject items that are:
- Minor updates, routine maintenance, or insignificant feature changes.
- Generic AI content, tutorials, lists, or SEO articles without a meaningful new event.
- Marketing claims without a concrete announcement or verifiable information.
- Repeated announcements, old news, or previously reported developments.
- AI-related but not useful or significant enough for a specialized AI news channel.

IMPORTANT EXCEPTION - ALWAYS ACCEPT:
If the news is about a NEW AI model, NEW AI tool, or a NEW VERSION of an existing
AI model/tool - even from a small or unfamiliar company - ALWAYS accept it as TOOL.
The release of a new AI model or version is always considered significant news
for an AI-focused channel, regardless of the company's reputation or size.
Only reject if it is a minor patch (bug fix) or a trivial cosmetic change.

Accept meaningful developments even from small or unfamiliar sources.
Do not judge importance based only on the reputation of the source.

STEP 4 - CLASSIFY EACH ACCEPTED ITEM INTO ONE CATEGORY:

TOOL:
New AI tools, models, products, services, major features,
meaningful integrations, availability, pricing, or regional rollouts.

RESEARCH:
New research papers, significant technical results,
benchmarks, or scientific breakthroughs.
Reject routine papers with no meaningful result.

CODING:
AI coding assistants, autonomous agents, developer tools,
open-source AI projects, and meaningful coding model updates.

COMPANY:
Important AI company news, funding, acquisitions, partnerships,
leadership changes, layoffs, lawsuits, security incidents,
and significant business or policy developments.

Choose exactly ONE category.
If categories overlap, choose the one most relevant to the main event.

STEP 5 - WRITE THE PERSIAN SUMMARY:
Write a concise, factual, natural Persian Telegram news summary.

Requirements:
- Write a clear and informative Persian headline.
- Headline should normally be under 12 words.
- Summary should normally be 2-3 short sentences (30-60 Persian words).
- Explain what happened and what is actually new.
- Include important names, model versions, dates, prices,
  availability, or technical results only when provided.
- Explain practical significance when supported by the source.
- Avoid clickbait, exaggeration, promotional language, and repetition.
- Do not begin with phrases like "در خبری جدید" or "به تازگی اعلام شد".
- Do not add unsupported opinions or predictions.
- Do not translate technical names or product names incorrectly.
- Do not claim a product is available if it was only announced.
- If a detail is unknown, omit it instead of guessing.

STEP 6 - OUTPUT:
Return ONLY a valid JSON array.
No markdown, explanations, or additional text.

For each item, use this exact structure:
{
  "id": 1,
  "category": "TOOL",
  "summary_fa": "عنوان فارسی خبر\\nمتن خلاصه فارسی"
}

For duplicates:
{
  "id": 2,
  "category": "DUPLICATE",
  "summary_fa": null
}

For rejected items:
{
  "id": 3,
  "category": null,
  "summary_fa": null
}

Return exactly one result for every input ID.
Do not change or omit IDs.

News items:
__ITEMS__
"""


def _build_items_block(news_batch):
    lines = []
    for item in news_batch:
        lines.append(f"ID: {item['id']}")
        lines.append(f"Title: {item['title']}")
        lines.append(f"Summary: {item['summary'][:200]}")
        lines.append("---")
    return "\n".join(lines)


def _call_ai(api_key, prompt):
    return requests.post(
        AI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000,
        },
        timeout=60,
    )


def _parse_response(content):
    clean = re.sub(r"```json\s*|\s*```", "", content).strip()
    m = re.search(r"\[.*\]", clean, re.DOTALL)
    if m:
        clean = m.group(0)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    if clean.count('"') % 2 != 0:
        clean += '"'
    if not clean.endswith("]"):
        clean = clean.rstrip(", \n") + "}]"
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return []


def _process_batch(news_batch):
    items_block = _build_items_block(news_batch)
    prompt = PROMPT_TEMPLATE.replace("__ITEMS__", items_block)

    for i, api_key in enumerate(AI_API_KEYS):
        try:
            resp = _call_ai(api_key, prompt)

            if resp.status_code == 429:
                print(f"[KEY {i+1} RATE LIMIT] switching...")
                continue

            if resp.status_code != 200:
                print(f"[KEY {i+1} ERROR] HTTP {resp.status_code}")
                continue

            data = resp.json()
            if "choices" not in data:
                print(f"[KEY {i+1}] no choices in response")
                continue

            content = data["choices"][0]["message"]["content"]
            print(f"[AI BATCH] got response len={len(content)}")

            parsed = _parse_response(content)
            if not isinstance(parsed, list):
                print(f"[BATCH] parsed is not a list")
                continue

            return parsed

        except Exception as e:
            print(f"[KEY {i+1} ERROR] {type(e).__name__}")
            continue

    print("[ALL KEYS FAILED]")
    return None


def classify_batch(news_list, batch_size=10):
    results = {}

    for start in range(0, len(news_list), batch_size):
        batch = news_list[start:start + batch_size]
        parsed = _process_batch(batch)

        if not parsed:
            continue

        for entry in parsed:
            try:
                item_id = entry.get("id")
                cat_raw = entry.get("category")
                summary_fa = entry.get("summary_fa") or ""

                cat_upper = str(cat_raw).strip().upper()
                if cat_upper not in VALID_CATS:
                    continue

                mapping = {
                    "TOOL":     CATEGORIES[0],
                    "RESEARCH": CATEGORIES[1],
                    "CODING":   CATEGORIES[2],
                    "COMPANY":  CATEGORIES[3],
                }

                results[item_id] = {
                    "category": mapping[cat_upper],
                    "summary_fa": summary_fa,
                }
            except Exception:
                continue

    return results
