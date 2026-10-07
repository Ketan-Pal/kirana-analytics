import json
import re
import difflib
from typing import Optional, Dict, Any
from database import get_connection

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())

def match_catalog_item(raw_name: str, standard_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Matches raw or standardized item text against known catalog products in Supabase."""
    clean_raw = clean_text(raw_name)
    clean_std = clean_text(standard_name or "")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, category, standard_unit, default_price, seasonality_tag, aliases FROM catalog_items")
            all_items = cur.fetchall()
    finally:
        conn.close()

    best_item = None
    best_score = 0.0

    for item in all_items:
        item_name_clean = clean_text(item["name"])
        raw_aliases = item["aliases"]
        aliases = []
        if isinstance(raw_aliases, list):
            aliases = [clean_text(str(a)) for a in raw_aliases]
        elif isinstance(raw_aliases, str):
            try:
                aliases = [clean_text(a) for a in json.loads(raw_aliases or "[]")]
            except Exception:
                pass

        # Exact alias match
        if clean_raw in aliases or (clean_std and clean_std in aliases):
            return item

        score_raw = difflib.SequenceMatcher(None, clean_raw, item_name_clean).ratio()
        score_std = difflib.SequenceMatcher(None, clean_std, item_name_clean).ratio() if clean_std else 0.0

        for a in aliases:
            a_score = max(
                difflib.SequenceMatcher(None, clean_raw, a).ratio(),
                difflib.SequenceMatcher(None, clean_std, a).ratio() if clean_std else 0.0
            )
            if a_score > score_raw:
                score_raw = a_score

        composite_score = max(score_raw, score_std)
        if composite_score > best_score:
            best_score = composite_score
            best_item = item

    if best_score >= 0.55 and best_item:
        return best_item

    return None

def auto_register_catalog_item(raw_name: str, standard_name: str, category: str, unit_price: float, unit: str) -> Dict[str, Any]:
    """Auto-creates new item in Supabase catalog_items if unknown."""
    conn = get_connection()
    try:
        name = standard_name.strip() if standard_name else raw_name.strip()
        price = unit_price if unit_price > 0 else 50.0
        aliases_json = json.dumps([clean_text(raw_name), clean_text(standard_name)])

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO catalog_items (name, category, standard_unit, default_price, seasonality_tag, aliases)
                VALUES (%s, %s, %s, %s, 'All-Season', %s::jsonb)
                ON CONFLICT (name) DO UPDATE SET default_price = EXCLUDED.default_price
                RETURNING id, name, category, standard_unit, default_price, seasonality_tag;
            """, (name, category or "Other", unit or "packet", price, aliases_json))
            new_item = cur.fetchone()
        conn.commit()
        return dict(new_item)
    finally:
        conn.close()
