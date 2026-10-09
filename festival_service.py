import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from database import get_connection

CALENDAR_API_BASE = "https://calendar-api-d7a8.onrender.com/v1/holidays"

FESTIVAL_DEFINITIONS = [
    {
        "key": "diwali",
        "name": "Diwali & Dhanteras Festive Surge",
        "match_keywords": ["diwali", "deepavali", "dhanteras"],
        "default_month": 11,
        "default_day": 8,
        "prep_lead_days": 21,
        "surge_categories": ["Sweets & Baking", "Staples", "Dry Fruits", "Snacks"],
        "surge_items": [
            {"item": "Sugar (Loose)", "surge_pct": 180, "prep_advice": "Stock 2.5x normal sugar volume for festive mithai and home baking."},
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 240, "prep_advice": "Peak demand for laddoos and festive snacks."},
            {"item": "Amul Pure Ghee 1L", "surge_pct": 210, "prep_advice": "Essential festive ingredient; price increases common close to Dhanteras."},
            {"item": "India Gate Basmati Rice 1kg", "surge_pct": 150, "prep_advice": "Bulk festival dinner replenishment."}
        ]
    },
    {
        "key": "navratri",
        "name": "Navratri & Fasting (Vrat) Season",
        "match_keywords": ["dussehra (mahashtami)", "mahashtami", "navratri"],
        "default_month": 10,
        "default_day": 19,
        "prep_lead_days": 14,
        "surge_categories": ["Fasting Essentials", "Dairy"],
        "surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 160, "prep_advice": "Crucial for fasting preparations and pooja."},
            {"item": "Amul Masti Dahi 400g", "surge_pct": 140, "prep_advice": "High consumption during fasting days."},
            {"item": "Tata Salt 1kg", "surge_pct": -40, "prep_advice": "Normal salt demand dips; substitute with Rock Salt (Sendha Namak)."}
        ]
    },
    {
        "key": "makar_sankranti",
        "name": "Makar Sankranti & Winter Harvest",
        "match_keywords": ["makar sankranti", "magha bihu", "pongal"],
        "default_month": 1,
        "default_day": 14,
        "prep_lead_days": 10,
        "surge_categories": ["Winter Staples", "Jaggery & Til"],
        "surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 150, "prep_advice": "Winter staple for laddu and khichdi preparations."},
            {"item": "Brooke Bond Red Label Tea 250g", "surge_pct": 135, "prep_advice": "Peak winter morning consumption."}
        ]
    },
    {
        "key": "holi",
        "name": "Holi Festival of Colors",
        "match_keywords": ["holi", "holika dahan"],
        "default_month": 3,
        "default_day": 4,
        "prep_lead_days": 14,
        "surge_categories": ["Staples", "Beverages", "Snacks"],
        "surge_items": [
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 175, "prep_advice": "High demand for Gujiya, namkeen, and pakoda preparation."},
            {"item": "Fortune Mustard Oil 1L", "surge_pct": 140, "prep_advice": "Frying surge for home snacks."},
            {"item": "Thums Up 250ml Bottle", "surge_pct": 160, "prep_advice": "Host party and celebration cold drink packs."}
        ]
    },
    {
        "key": "raksha_bandhan",
        "name": "Raksha Bandhan Sweets Rush",
        "match_keywords": ["raksha bandhan"],
        "default_month": 8,
        "default_day": 28,
        "prep_lead_days": 10,
        "surge_categories": ["Sweets & Dairy", "Snacks"],
        "surge_items": [
            {"item": "Sugar (Loose)", "surge_pct": 160, "prep_advice": "Peak mithai and sweet gift preparation demand."},
            {"item": "Amul Pure Ghee 1L", "surge_pct": 150, "prep_advice": "Fresh halwai and home preparation surge."}
        ]
    },
    {
        "key": "janmashtami",
        "name": "Janmashtami Fasting & Pooja",
        "match_keywords": ["janmashtami"],
        "default_month": 9,
        "default_day": 4,
        "prep_lead_days": 7,
        "surge_categories": ["Dairy", "Dry Fruits"],
        "surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 150, "prep_advice": "Pooja and prasad preparations."},
            {"item": "Amul Taaza Milk 500ml", "surge_pct": 130, "prep_advice": "Panchamrit preparation surge."}
        ]
    },
    {
        "key": "eid",
        "name": "Eid Festive Feast & Refreshment",
        "match_keywords": ["id-ul-fitr", "id- ul- fitr"],
        "default_month": 3,
        "default_day": 21,
        "prep_lead_days": 14,
        "surge_categories": ["Staples", "Dairy", "Beverages"],
        "surge_items": [
            {"item": "Amul Taaza Milk 500ml", "surge_pct": 160, "prep_advice": "Sewai and sheer khurma cooking surge."},
            {"item": "Sugar (Loose)", "surge_pct": 150, "prep_advice": "Dessert preparations."}
        ]
    },
    {
        "key": "summer",
        "name": "Summer Heatwave & Refreshment Surge",
        "match_keywords": [],
        "default_month": 5,
        "default_day": 10,
        "prep_lead_days": 15,
        "surge_categories": ["Beverages", "Dairy"],
        "surge_items": [
            {"item": "Sting Energy Drink 250ml", "surge_pct": 220, "prep_advice": "Peak cooling & energy drink demand from youth & workers."},
            {"item": "Amul Masti Dahi 400g", "surge_pct": 170, "prep_advice": "Chaas, lassi, and cooling lunch staple."},
            {"item": "Thums Up 250ml Bottle", "surge_pct": 180, "prep_advice": "Increase refrigerator shelf space by 50%."}
        ]
    },
    {
        "key": "monsoon",
        "name": "Monsoon Chai & Pakoda Season",
        "match_keywords": [],
        "default_month": 7,
        "default_day": 15,
        "prep_lead_days": 15,
        "surge_categories": ["Beverages", "Snacks", "Staples"],
        "surge_items": [
            {"item": "Brooke Bond Red Label Tea 250g", "surge_pct": 160, "prep_advice": "Consistent all-day tea consumption during rainy weeks."},
            {"item": "Maggi 2-Minute Noodles 70g", "surge_pct": 180, "prep_advice": "Instant comfort food surge for school kids and evening snacks."},
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 150, "prep_advice": "Pakoda and monsoon frying demand."}
        ]
    }
]

def sync_festival_calendar_if_needed(year: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
    """
    Synchronizes the festival calendar with the Official Indian Regional Calendar API:
    GET https://calendar-api-d7a8.onrender.com/v1/holidays?country=IN&region=UP&year={year}
    
    STRICT RATE LIMIT ENFORCEMENT:
    - Checks Supabase first.
    - If the year has been synchronized within the last 30 days, skips API call entirely.
    - Maximum sync frequency: at most once a month.
    """
    target_year = year or datetime.now().year
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check if this year was synced within last 30 days
            cur.execute("""
                SELECT COUNT(*) as count, MAX(updated_at) as last_updated
                FROM festival_calendar
                WHERE calendar_year = %s;
            """, (target_year,))
            row = cur.fetchone()
            count = row["count"] if row else 0
            last_updated = row["last_updated"] if row else None

            if not force and count >= 5 and last_updated:
                # If updated in last 30 days, skip
                days_since_update = (datetime.now(last_updated.tzinfo) - last_updated).days
                if days_since_update < 30:
                    return {
                        "status": "skipped",
                        "reason": f"Festival calendar for {target_year} is fresh (synced {days_since_update} days ago). Rate limits preserved."
                    }

        # Sync needed: call API once
        holidays_data = []
        source_label = "india.gov.in"
        api_url = f"{CALENDAR_API_BASE}?country=IN&region=UP&year={target_year}"
        
        try:
            # Render free tier takes 15-25s on cold start; 25s timeout accommodates spin-up
            with httpx.Client(timeout=25.0) as client:
                resp = client.get(api_url)
                if resp.status_code == 200:
                    holidays_data = resp.json().get("data", [])
        except Exception as e:
            print(f"[Festival Sync] Warning: External Calendar API unreachable: {e}. Falling back to baseline.")

        # Process each festival definition
        synced_count = 0
        with conn.cursor() as cur:
            for f_def in FESTIVAL_DEFINITIONS:
                resolved_date_str = None

                # Search in official holidays from API
                if holidays_data and f_def["match_keywords"]:
                    for h in holidays_data:
                        h_name_lower = h.get("name", "").lower()
                        if any(kw in h_name_lower for kw in f_def["match_keywords"]):
                            resolved_date_str = h.get("date")
                            break

                # Fallback to default calendar date if not found in API
                if not resolved_date_str:
                    resolved_date_str = f"{target_year}-{f_def['default_month']:02d}-{f_def['default_day']:02d}"

                cur.execute("""
                    INSERT INTO festival_calendar (
                        festival_name, calendar_year, festival_date, prep_lead_days,
                        surge_categories, surge_items, source, updated_at
                    ) VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (festival_name, calendar_year) DO UPDATE
                    SET festival_date = EXCLUDED.festival_date,
                        prep_lead_days = EXCLUDED.prep_lead_days,
                        surge_categories = EXCLUDED.surge_categories,
                        surge_items = EXCLUDED.surge_items,
                        source = EXCLUDED.source,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    f_def["name"],
                    target_year,
                    resolved_date_str,
                    f_def["prep_lead_days"],
                    json.dumps(f_def["surge_categories"]),
                    json.dumps(f_def["surge_items"]),
                    source_label
                ))
                synced_count += 1

            conn.commit()

        return {
            "status": "success",
            "year": target_year,
            "festivals_synced": synced_count,
            "source": source_label
        }
    finally:
        conn.close()

def get_festival_roadmap() -> Dict[str, Any]:
    """
    Provides forward roadmap for upcoming seasons and major Indian festivals.
    Queries 100% locally from Supabase festival_calendar table (0 external API calls).
    """
    today = datetime.now().date()
    current_year = today.year

    # Ensure current year & next year exist in DB (executes sync once a month max)
    try:
        sync_festival_calendar_if_needed(current_year)
        if today.month >= 10:
            sync_festival_calendar_if_needed(current_year + 1)
    except Exception as e:
        print(f"[Festival Roadmap] Auto-sync check warning: {e}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    festival_name,
                    festival_date,
                    prep_lead_days,
                    surge_categories,
                    surge_items,
                    source
                FROM festival_calendar
                WHERE festival_date >= %s
                ORDER BY festival_date ASC
                LIMIT 8;
            """, (today,))
            rows = cur.fetchall()
    finally:
        conn.close()

    upcoming_festivals = []
    for r in rows:
        fest_date = r["festival_date"]
        days_until = (fest_date - today).days

        if days_until <= 30:
            status = "CRITICAL: Stock Within 7 Days"
            urgency_color = "rose"
        elif days_until <= 60:
            status = "UPCOMING: Plan Distributor Allotment"
            urgency_color = "amber"
        else:
            status = "ADVANCE: Scheduled Outlook"
            urgency_color = "blue"

        s_cats = r["surge_categories"]
        if isinstance(s_cats, str):
            s_cats = json.loads(s_cats)

        s_items = r["surge_items"]
        if isinstance(s_items, str):
            s_items = json.loads(s_items)

        upcoming_festivals.append({
            "name": r["festival_name"],
            "target_date": fest_date.strftime("%d %b %Y"),
            "days_until": days_until,
            "status": status,
            "urgency_color": urgency_color,
            "surge_categories": s_cats or [],
            "key_items": s_items or [],
            "source": r.get("source") or "Baseline"
        })

    return {
        "current_date": today.strftime("%d-%b-%Y"),
        "roadmap": upcoming_festivals
    }
