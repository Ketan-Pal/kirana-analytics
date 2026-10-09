import os
import re
import json
import time
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

from database import get_connection
from gemini_enricher import PRIMARY_MODEL, CANDIDATE_MODELS

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def generate_search_queries(festival_name: str, year: int) -> List[str]:
    """Uses Gemini to formulate 3 high-yield FMCG market search queries for DuckDuckGo."""
    prompt = f"""You are an Indian FMCG and Kirana retail research expert.
We want to discover the latest market trends, consumer shifts, and trending grocery/snack/gifting items for {festival_name} in India for year {year}.

Formulate exactly 3 distinct, high-precision web search queries to discover:
1. Emerging packaged gift hampers, sweets, and confectionery trends.
2. Fast-moving cooking ingredients, staples, and fasting items.
3. Trending beverages, namkeen, and celebration snacks.

Return ONLY a JSON array of 3 strings. Example:
[
  "{festival_name} {year} FMCG packaged sweets gifting trends India",
  "fastest selling grocery snacks beverages {festival_name} {year} India",
  "Kirana retail festive demand surge trends {festival_name} {year}"
]"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    for model in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
                    clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                    queries = json.loads(clean_json)
                    if isinstance(queries, list) and len(queries) >= 2:
                        return queries[:3]
        except Exception as e:
            print(f"[Trend Crawler] Query generation fallback from {model}: {e}")
            continue

    # Fallback default queries
    return [
        f"{festival_name} {year} FMCG packaged sweets gifting trends India",
        f"fastest selling grocery snacks {festival_name} {year} India Kirana",
        f"festive demand consumer buying trends {festival_name} {year} India"
    ]

def fetch_duckduckgo_snippets(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Performs keyless, free web search via DuckDuckGo HTML endpoint."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    results = []
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers)
            if resp.status_code == 200:
                html = resp.text
                # Extract results: title and snippet
                titles = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                for t in titles[:max_results]:
                    clean_t = re.sub(r'<[^>]+>', '', t).strip()
                    if clean_t:
                        results.append({"query": query, "snippet": clean_t})
    except Exception as e:
        print(f"[Trend Crawler] DuckDuckGo fetch warning for '{query}': {e}")

    return results

def synthesize_festival_trends(festival_name: str, year: int, snippets: List[Dict[str, str]]) -> Dict[str, Any]:
    """Feeds web search snippets back to Gemini to aggregate into structured Kirana stocking recommendations."""
    snippet_text = "\n".join([f"- ({s.get('query')}) {s.get('snippet')}" for s in snippets]) if snippets else "No external search snippets available; rely on modern FMCG domain intelligence."

    prompt = f"""You are a master Indian Retail & FMCG Consultant for neighborhood Kirana stores.
Analyze the following real-time web search findings for {festival_name} {year} in India:

### Recent Web Search Findings:
{snippet_text}

### Your Goal:
Synthesize the latest consumer demand shifts and trending FMCG products for {festival_name} {year}.
Modernize traditional retail definitions (e.g., incorporate packaged chocolate gifting like Cadbury Celebrations, premium dry fruits, branded ghee, tetra juices, roasted snacks alongside core staples).

Return ONLY valid JSON matching this exact schema:
{{
  "market_shift_summary": "2-3 sentences explaining the latest shift in consumer gifting, hosting, or cooking preferences for this festival.",
  "trending_categories": ["Category 1", "Category 2", "Category 3"],
  "surge_items": [
    {{
      "item": "Product Name (e.g. Cadbury Celebrations Box or Amul Pure Ghee 1L)",
      "surge_pct": 180,
      "prep_advice": "Specific stocking or distributor ordering advice (e.g. Order 3 cartons 14 days ahead before wholesale rates surge).",
      "trend_reason": "Why customers are buying this specifically in modern times."
    }}
  ]
}}"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    for model in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            with httpx.Client(timeout=25.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
                    clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                    parsed = json.loads(clean_json)
                    parsed["_source"] = f"DuckDuckGo + {model}"
                    parsed["_snippets_count"] = len(snippets)
                    return parsed
        except Exception as e:
            print(f"[Trend Crawler] Synthesis fallback from {model}: {e}")
            continue

    # Deterministic fallback
    return {
        "market_shift_summary": f"Strong consumer demand across branded gifting, packaged sweets, and festival feast staples for {festival_name}.",
        "trending_categories": ["Sweets & Baking", "Staples", "Snacks"],
        "surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 180, "prep_advice": "Order 2 cartons ahead of festival wholesale rush.", "trend_reason": "Core cooking & pooja staple."},
            {"item": "Sugar (Loose)", "surge_pct": 150, "prep_advice": "Stock extra 50kg bags for home dessert making.", "trend_reason": "High household consumption."}
        ],
        "_source": "Deterministic FMCG Baseline",
        "_snippets_count": 0
    }

def crawl_and_update_festival_trend(festival_name: str, year: int, force: bool = False) -> Dict[str, Any]:
    """
    Executes the full agentic loop:
    1. Formulates search queries via Gemini
    2. Searches DuckDuckGo (Free / No key)
    3. Aggregates and synthesizes with Gemini
    4. Updates Supabase festival_calendar table
    """
    conn = get_connection()
    try:
        # Check if already enriched recently
        if not force:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT surge_items, updated_at
                    FROM festival_calendar
                    WHERE festival_name ILIKE %s AND calendar_year = %s;
                """, (f"%{festival_name}%", year))
                row = cur.fetchone()
                if row and row["surge_items"]:
                    # If updated in last 14 days, skip
                    days_old = (datetime.now(row["updated_at"].tzinfo) - row["updated_at"]).days
                    if days_old < 14:
                        return {
                            "status": "cached",
                            "message": f"Trend intelligence for {festival_name} {year} was refreshed {days_old} days ago. Skipping."
                        }

        # Step 1: Formulate search queries
        queries = generate_search_queries(festival_name, year)

        # Step 2: Query DuckDuckGo
        all_snippets = []
        for q in queries:
            snippets = fetch_duckduckgo_snippets(q, max_results=3)
            all_snippets.extend(snippets)
            time.sleep(0.5)  # respectful delay between searches

        # Step 3: Synthesize with Gemini
        synthesis = synthesize_festival_trends(festival_name, year, all_snippets)

        # Step 4: Persist in Supabase
        with conn.cursor() as cur:
            source_tag = synthesis.get("_source", "DuckDuckGo + Gemini")
            cur.execute("""
                UPDATE festival_calendar
                SET surge_categories = %s::jsonb,
                    surge_items = %s::jsonb,
                    source = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE festival_name ILIKE %s AND calendar_year = %s;
            """, (
                json.dumps(synthesis.get("trending_categories", [])),
                json.dumps(synthesis.get("surge_items", [])),
                source_tag,
                f"%{festival_name}%",
                year
            ))
            conn.commit()

        return {
            "status": "success",
            "festival": festival_name,
            "year": year,
            "queries_executed": len(queries),
            "snippets_analyzed": len(all_snippets),
            "synthesis": synthesis
        }
    finally:
        conn.close()
