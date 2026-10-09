import os
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from database import get_connection
from analytics import (
    get_basket_co_purchases,
    get_day_of_week_patterns,
    get_weather_impact_analysis,
    get_changing_trend_patterns,
)
from forecasting import (
    get_next_month_forecast,
    get_seasonal_and_festival_roadmap,
)

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

CANDIDATE_MODELS = ["gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-flash-latest"]
PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

def get_cached_insights() -> Optional[Dict[str, Any]]:
    """Retrieves the latest cached AI insights from Supabase."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT insights_json, updated_at, model_used
                FROM ai_insights_cache
                WHERE cache_key = 'latest_enrichment'
                ORDER BY id DESC
                LIMIT 1;
            """)
            row = cur.fetchone()
            if row:
                data = row["insights_json"]
                if isinstance(data, str):
                    data = json.loads(data)
                data["_cached_at"] = str(row["updated_at"])
                data["_model"] = row["model_used"]
                return data
            return None
    except Exception as e:
        print(f"[AI Cache] Error reading cache: {e}")
        return None
    finally:
        conn.close()

def save_insights_to_cache(insights: Dict[str, Any], model_used: str = PRIMARY_MODEL):
    """Stores or updates the latest enriched insights in Supabase."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ai_insights_cache (cache_key, updated_at, insights_json, model_used)
                VALUES ('latest_enrichment', CURRENT_TIMESTAMP, %s::jsonb, %s)
                ON CONFLICT (cache_key) DO UPDATE
                SET updated_at = CURRENT_TIMESTAMP,
                    insights_json = EXCLUDED.insights_json,
                    model_used = EXCLUDED.model_used;
            """, (json.dumps(insights), model_used))
        conn.commit()
    except Exception as e:
        print(f"[AI Cache] Error saving to cache: {e}")
    finally:
        conn.close()

def build_synthesis_prompt(context_data: Dict[str, Any]) -> str:
    """Builds the prompt that guides Gemini to act as a senior Indian Kirana retail consultant."""
    raw_baskets = context_data.get('baskets', [])
    if isinstance(raw_baskets, dict):
        baskets_sample = raw_baskets.get('patterns', [])[:5] if not raw_baskets.get('is_gated') else [{"status": raw_baskets.get("message")}]
    else:
        baskets_sample = raw_baskets[:5] if isinstance(raw_baskets, list) else []

    return f"""You are a master Indian Retail & FMCG Business Consultant specializing in Kirana stores and neighbourhood convenience retail.

Analyze the following live mathematical sales patterns and forecast data collected from the store:

### 1. Customer Basket Co-Purchases (What sells together in bills):
{json.dumps(baskets_sample, indent=2)}

### 2. Product Growth Momentum (Surging vs. Declining in last 30 days):
{json.dumps(context_data.get('trends', {}), indent=2)}

### 3. Weather Demand Sensitivities (Units/day observed):
{json.dumps(context_data.get('weather', []), indent=2)}

### 4. Next Month Projected Demand by SKU:
{json.dumps(context_data.get('forecast', {}).get('forecast_items', [])[:6], indent=2)}

### 5. Upcoming Festivals & Days Remaining:
{json.dumps(context_data.get('festivals', {}).get('roadmap', [])[:3], indent=2)}

---

### Your Objective:
Transform these raw mathematical numbers into strategic, high-value, actionable retail advice for the store owner.
Write in professional English with natural Indian Kirana & FMCG retail terminology.

Return ONLY a valid JSON object matching this exact schema:
{{
  "daily_executive_summary": "2-3 sentences of clear strategic guidance for today's counter operations.",
  "weather_tactical_action": {{
    "headline": "Short title (e.g. Rain Preparation Alert)",
    "action_directive": "Exact counter/shelving action the shopkeeper should execute right now.",
    "priority_items": ["Item 1", "Item 2"]
  }},
  "merchandising_combos": [
    {{
      "combo_name": "Catchy Indian promo name (e.g. Monsoon Evening Hunger Combo)",
      "items": "Item A + Item B",
      "consumer_behavior": "Why customers are buying these together (consumer habit / time-of-day habit).",
      "suggested_promo": "Specific combo deal with discount in Rupees (e.g. Save Rs 5).",
      "shelf_placement_directive": "Where exactly to place them in a typical 150-300 sq.ft. Kirana store."
    }}
  ],
  "procurement_distributor_advice": [
    {{
      "product": "Product name",
      "recommended_action": "Order X cartons / bulk bags before festival rush.",
      "distributor_timing_tip": "Why to order now vs later (distributor price surge, lead-time bottleneck)."
    }}
  ],
  "trend_insights": [
    {{
      "product": "Product name",
      "trend_direction": "Surging | Declining",
      "momentum": "+X%",
      "retail_explanation": "Real-world reason why consumer demand is shifting."
    }}
  ]
}}
"""

def generate_fallback_insights(context_data: Dict[str, Any]) -> Dict[str, Any]:
    raw_baskets = context_data.get("baskets", [])
    top_baskets = raw_baskets if isinstance(raw_baskets, list) else (raw_baskets.get("patterns", []) if isinstance(raw_baskets, dict) else [])
    pair_str = f"{top_baskets[0]['item_a']} + {top_baskets[0]['item_b']}" if (top_baskets and isinstance(top_baskets[0], dict) and 'item_a' in top_baskets[0]) else "Maggi + Thums Up"

    return {
        "daily_executive_summary": "Focus counter space on high-velocity evening snack pairs and check safety stock for upcoming festival essentials. Demand momentum is positive across branded staples.",
        "weather_tactical_action": {
            "headline": "Seasonal Demand Alignment",
            "action_directive": "Position hot beverages, instant comfort noodles, and biscuits on eye-level shelves near the entrance.",
            "priority_items": ["Brooke Bond Red Label Tea", "Maggi 2-Minute Noodles"]
        },
        "merchandising_combos": [
            {
                "combo_name": "Evening Refreshment Pair",
                "items": pair_str,
                "consumer_behavior": "Customers frequently bundle instant comfort snacks with beverages during evening rush hours.",
                "suggested_promo": f"Offer {pair_str} with a ₹5 instant combo discount.",
                "shelf_placement_directive": "Place both products side-by-side on the eye-level front glass counter."
            }
        ],
        "procurement_distributor_advice": [
            {
                "product": "Sugar & Besan",
                "recommended_action": "Advance wholesale booking of 5x 50kg bags.",
                "distributor_timing_tip": "Book with distributors 14 days ahead of festival dates before wholesale prices rise."
            }
        ],
        "trend_insights": [
            {
                "product": "Sting Energy Drink",
                "trend_direction": "Surging",
                "momentum": "+45%",
                "retail_explanation": "Strong youth and on-the-go afternoon refresh demand."
            }
        ],
        "_is_fallback": True
    }

def enrich_analytics_with_gemini(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Orchestrates AI enrichment: checks cache first, queries Gemini if invalid/forced,
    and provides a deterministic fallback on failure.
    """
    if not force_refresh:
        cached = get_cached_insights()
        if cached:
            return cached

    # Gather live mathematical aggregates from Supabase
    context_data = {
        "baskets": get_basket_co_purchases(min_pairs=2),
        "days": get_day_of_week_patterns(),
        "weather": get_weather_impact_analysis(),
        "trends": get_changing_trend_patterns(),
        "forecast": get_next_month_forecast(),
        "festivals": get_seasonal_and_festival_roadmap(),
    }

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[AI Enricher] GEMINI_API_KEY not configured. Using fallback.")
        return generate_fallback_insights(context_data)

    prompt = build_synthesis_prompt(context_data)

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.3
        }
    }

    models_to_try = [PRIMARY_MODEL] + [m for m in CANDIDATE_MODELS if m != PRIMARY_MODEL]
    last_error = None

    for model_name in models_to_try:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            start_t = time.time()
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{api_url}?key={api_key}", json=payload)
                resp.raise_for_status()

                res_json = resp.json()
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                enriched_result = json.loads(raw_text)

                latency_ms = int((time.time() - start_t) * 1000)
                enriched_result["_latency_ms"] = latency_ms
                enriched_result["_model"] = model_name
                enriched_result["_is_fallback"] = False

                save_insights_to_cache(enriched_result, model_name)
                print(f"[AI Enricher] Successfully generated and cached AI insights using {model_name} in {latency_ms}ms")
                return enriched_result

        except Exception as e:
            last_error = e
            print(f"[AI Enricher] Model '{model_name}' attempt failed: {e}. Trying fallback model...")

    print(f"[AI Enricher] All Gemini model attempts failed ({last_error}). Falling back to baseline.")
    fallback = generate_fallback_insights(context_data)
    fallback["_error"] = str(last_error)
    return fallback


if __name__ == "__main__":
    print("Testing Gemini Analytics Enricher...")
    res = enrich_analytics_with_gemini(force_refresh=True)
    print("\n--- ENRICHED INSIGHTS ---")
    print(json.dumps(res, indent=2))
