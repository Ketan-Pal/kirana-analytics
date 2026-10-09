from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_connection

FESTIVAL_CALENDAR = [
    {
        "name": "Diwali & Dhanteras Festive Surge",
        "month": 11,
        "day": 1,
        "surge_categories": ["Sweets & Baking", "Staples", "Dry Fruits", "Snacks"],
        "high_surge_items": [
            {"item": "Sugar (Loose)", "surge_pct": 180, "prep_advice": "Stock 2.5x normal sugar volume for festive mithai and home baking."},
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 240, "prep_advice": "Peak demand for laddoos and festive snacks."},
            {"item": "Amul Pure Ghee 1L", "surge_pct": 210, "prep_advice": "Essential festive ingredient; price increases common close to Dhanteras."},
            {"item": "India Gate Basmati Rice 1kg", "surge_pct": 150, "prep_advice": "Bulk festival dinner replenishment."}
        ]
    },
    {
        "name": "Navratri & Fasting (Vrat) Season",
        "month": 10,
        "day": 12,
        "surge_categories": ["Fasting Essentials", "Dairy"],
        "high_surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 160, "prep_advice": "Crucial for fasting preparations and pooja."},
            {"item": "Amul Masti Dahi 400g", "surge_pct": 140, "prep_advice": "High consumption during fasting days."},
            {"item": "Tata Salt 1kg", "surge_pct": -40, "prep_advice": "Normal salt demand dips; substitute with Rock Salt (Sendha Namak)."}
        ]
    },
    {
        "name": "Makar Sankranti & Winter Harvest",
        "month": 1,
        "day": 14,
        "surge_categories": ["Winter Staples", "Jaggery & Til"],
        "high_surge_items": [
            {"item": "Amul Pure Ghee 1L", "surge_pct": 150, "prep_advice": "Winter staple for laddu and khichdi preparations."},
            {"item": "Brooke Bond Red Label Tea 250g", "surge_pct": 135, "prep_advice": "Peak winter morning consumption."}
        ]
    },
    {
        "name": "Holi Festival of Colors",
        "month": 3,
        "day": 20,
        "surge_categories": ["Staples", "Beverages", "Snacks"],
        "high_surge_items": [
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 175, "prep_advice": "High demand for Gujiya, namkeen, and pakoda preparation."},
            {"item": "Fortune Mustard Oil 1L", "surge_pct": 140, "prep_advice": "Frying surge for home snacks."},
            {"item": "Thums Up 250ml Bottle", "surge_pct": 160, "prep_advice": "Host party and celebration cold drink packs."}
        ]
    },
    {
        "name": "Summer Heatwave & Refreshment Surge",
        "month": 5,
        "day": 10,
        "surge_categories": ["Beverages", "Dairy"],
        "high_surge_items": [
            {"item": "Sting Energy Drink 250ml", "surge_pct": 220, "prep_advice": "Peak cooling & energy drink demand from youth & workers."},
            {"item": "Amul Masti Dahi 400g", "surge_pct": 170, "prep_advice": "Chaas, lassi, and cooling lunch staple."},
            {"item": "Thums Up 250ml Bottle", "surge_pct": 180, "prep_advice": "Increase refrigerator shelf space by 50%."}
        ]
    },
    {
        "name": "Monsoon Chai & Pakoda Season",
        "month": 7,
        "day": 15,
        "surge_categories": ["Beverages", "Snacks", "Staples"],
        "high_surge_items": [
            {"item": "Brooke Bond Red Label Tea 250g", "surge_pct": 160, "prep_advice": "Consistent all-day tea consumption during rainy weeks."},
            {"item": "Maggi 2-Minute Noodles 70g", "surge_pct": 180, "prep_advice": "Instant comfort food surge for school kids and evening snacks."},
            {"item": "Besan (Gram Flour) 500g", "surge_pct": 150, "prep_advice": "Pakoda and monsoon frying demand."}
        ]
    }
]

from festival_service import get_festival_roadmap as get_festival_roadmap_from_db

def get_next_month_forecast() -> Dict[str, Any]:
    """
    Predicts next month's demand by SKU and Category from Supabase PostgreSQL.
    Features TASK-004: Early run-rate extrapolation during Days 1-29 cold-start.
    """
    conn = get_connection()
    try:
        today = datetime.now()
        d_30_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        with conn.cursor() as cur:
            # Check how many distinct days are recorded (cold-start detection)
            cur.execute("""
                SELECT COUNT(DISTINCT sale_date) as active_days
                FROM sale_items
                WHERE sale_date >= %s;
            """, (d_30_ago,))
            active_row = cur.fetchone()
            active_days = int(active_row["active_days"]) if active_row and active_row["active_days"] else 0

            cur.execute("""
                SELECT 
                    product_name,
                    category,
                    unit,
                    unit_price,
                    COALESCE(SUM(quantity), 0) as current_monthly_qty,
                    COALESCE(SUM(total_amount), 0.0) as current_monthly_rev
                FROM sale_items
                WHERE sale_date >= %s
                GROUP BY product_name, category, unit, unit_price;
            """, (d_30_ago,))
            rows = cur.fetchall()

            d_60_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
            cur.execute("""
                SELECT 
                    product_name,
                    COALESCE(SUM(quantity), 0) as prior_qty
                FROM sale_items
                WHERE sale_date BETWEEN %s AND %s
                GROUP BY product_name;
            """, (d_60_ago, d_30_ago))
            prior_map = {r["product_name"]: float(r["prior_qty"]) for r in cur.fetchall()}
    finally:
        conn.close()

    next_month_dt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    next_month_name = next_month_dt.strftime("%B %Y")
    next_month_int = next_month_dt.month

    if next_month_int in [3, 4, 5, 6]:
        target_season = "Summer"
    elif next_month_int in [7, 8, 9]:
        target_season = "Monsoon"
    elif next_month_int in [10, 11]:
        target_season = "Festive"
    else:
        target_season = "Winter"

    if not rows or active_days == 0:
        return {
            "target_month": next_month_name,
            "target_season": target_season,
            "total_projected_revenue": 0.0,
            "total_projected_units": 0,
            "forecast_items": [],
            "is_cold_start": True,
            "active_days": 0,
            "message": "Awaiting initial daily sales transactions to generate baseline run-rate forecast."
        }

    # TASK-004: Extrapolate daily run-rate if operating for fewer than 30 days
    extrapolation_multiplier = (30.0 / active_days) if (1 <= active_days < 30) else 1.0

    forecast_items = []
    total_projected_revenue = 0.0
    total_projected_units = 0

    for r in rows:
        name = r["product_name"]
        raw_curr_qty = float(r["current_monthly_qty"])
        
        # Apply 30-day run-rate extrapolation during early store weeks
        curr_qty = raw_curr_qty * extrapolation_multiplier
        prior_qty = prior_map.get(name, 0.0)
        price = float(r["unit_price"])

        if prior_qty > 0:
            growth_rate = (curr_qty - prior_qty) / prior_qty
            damped_growth = max(-0.25, min(0.35, growth_rate))
        else:
            # Baseline accumulating during first month
            damped_growth = 0.05

        predicted_qty = round(curr_qty * (1.0 + damped_growth))

        seasonal_lift = 1.0
        cat = r["category"]
        if target_season == "Summer" and (cat == "Beverages" or "Dahi" in name):
            seasonal_lift = 1.25
        elif target_season == "Monsoon" and ("Tea" in name or "Maggi" in name):
            seasonal_lift = 1.20
        elif target_season == "Winter" and ("Ghee" in name or "Tea" in name or "Oil" in name):
            seasonal_lift = 1.25
        elif target_season == "Festive" and (cat == "Staples" or "Sugar" in name or "Besan" in name):
            seasonal_lift = 1.30

        final_forecast_qty = max(3, int(predicted_qty * seasonal_lift))
        projected_rev = round(final_forecast_qty * price, 2)

        total_projected_revenue += projected_rev
        total_projected_units += final_forecast_qty

        extrapolation_note = f" (Extrapolated from {active_days}d run-rate)" if (1 <= active_days < 30) else ""

        forecast_items.append({
            "name": name,
            "category": cat,
            "current_month_qty": int(round(raw_curr_qty)),
            "projected_next_month_qty": final_forecast_qty,
            "unit": r["unit"],
            "unit_price": price,
            "projected_revenue": projected_rev,
            "growth_trend": round(((final_forecast_qty - curr_qty) / max(1.0, curr_qty)) * 100, 1),
            "stocking_action": f"Prepare inventory for ~{final_forecast_qty} {r['unit']}{extrapolation_note} ({'+' if final_forecast_qty > curr_qty else ''}{round(((final_forecast_qty - curr_qty) / max(1.0, curr_qty)) * 100)}% vs run-rate)"
        })

    forecast_items.sort(key=lambda x: x["projected_revenue"], reverse=True)

    return {
        "target_month": next_month_name,
        "target_season": target_season,
        "active_days": active_days,
        "is_extrapolated": 1 <= active_days < 30,
        "total_projected_revenue": round(total_projected_revenue, 2),
        "total_projected_units": total_projected_units,
        "forecast_items": forecast_items
    }

def get_seasonal_and_festival_roadmap() -> Dict[str, Any]:
    """
    Provides forward roadmap for upcoming seasons and major Indian festivals.
    Dynamically served from Supabase festival_calendar table (ADR-001).
    """
    try:
        db_roadmap = get_festival_roadmap_from_db()
        if db_roadmap and db_roadmap.get("roadmap"):
            return db_roadmap
    except Exception as e:
        print(f"[Roadmap] Fallback from database roadmap: {e}")

    # Fallback to local calendar if database table is initializing
    today = datetime.now()
    current_year = today.year
    upcoming_festivals = []

    for fest in FESTIVAL_CALENDAR:
        target_year = current_year if fest["month"] >= today.month else current_year + 1
        fest_date = datetime(target_year, fest["month"], fest["day"])
        days_until = (fest_date - today).days

        if days_until < 0:
            days_until += 365

        if days_until <= 30:
            status = "CRITICAL: Stock Within 7 Days"
            urgency_color = "rose"
        elif days_until <= 60:
            status = "UPCOMING: Plan Distributor Allotment"
            urgency_color = "amber"
        else:
            status = "ADVANCE: Scheduled Outlook"
            urgency_color = "blue"

        upcoming_festivals.append({
            "name": fest["name"],
            "target_date": fest_date.strftime("%d %b %Y"),
            "days_until": days_until,
            "status": status,
            "urgency_color": urgency_color,
            "surge_categories": fest["surge_categories"],
            "key_items": fest["high_surge_items"]
        })

    upcoming_festivals.sort(key=lambda x: x["days_until"])
    return {
        "current_date": today.strftime("%d-%b-%Y"),
        "roadmap": upcoming_festivals
    }
