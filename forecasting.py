from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_connection

# Comprehensive Indian Retail Festive Demand Calendar
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

def get_next_month_forecast() -> Dict[str, Any]:
    """
    Predicts next month's demand by SKU and Category:
    Combines baseline 30-day velocity, growth momentum, and seasonal weighting.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get past 30 days data
    today = datetime.now()
    d_30_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT 
            product_name,
            category,
            unit,
            unit_price,
            SUM(quantity) as current_monthly_qty,
            SUM(total_amount) as current_monthly_rev
        FROM sale_items
        WHERE sale_date >= ?
        GROUP BY product_name
    """, (d_30_ago,))
    rows = cursor.fetchall()

    # Prior 30-60 days for trend rate
    d_60_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT 
            product_name,
            SUM(quantity) as prior_qty
        FROM sale_items
        WHERE sale_date BETWEEN ? AND ?
        GROUP BY product_name
    """, (d_60_ago, d_30_ago))
    prior_map = {r["product_name"]: r["prior_qty"] for r in cursor.fetchall()}

    conn.close()

    # Target Next Month metadata
    next_month_dt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    next_month_name = next_month_dt.strftime("%B %Y")
    next_month_int = next_month_dt.month

    # Seasonal index for next month
    if next_month_int in [3, 4, 5, 6]:
        target_season = "Summer"
    elif next_month_int in [7, 8, 9]:
        target_season = "Monsoon"
    elif next_month_int in [10, 11]:
        target_season = "Festive"
    else:
        target_season = "Winter"

    forecast_items = []
    total_projected_revenue = 0.0
    total_projected_units = 0

    for r in rows:
        name = r["product_name"]
        curr_qty = r["current_monthly_qty"]
        prior_qty = prior_map.get(name, curr_qty)
        price = r["unit_price"]

        # Calculate momentum multiplier
        if prior_qty > 0:
            growth_rate = (curr_qty - prior_qty) / prior_qty
            # Dampen extreme spikes
            damped_growth = max(-0.25, min(0.35, growth_rate))
        else:
            damped_growth = 0.05

        # Base forecasted quantity
        predicted_qty = round(curr_qty * (1.0 + damped_growth))

        # Apply upcoming seasonal lift
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

        final_forecast_qty = max(5, int(predicted_qty * seasonal_lift))
        projected_rev = round(final_forecast_qty * price, 2)

        total_projected_revenue += projected_rev
        total_projected_units += final_forecast_qty

        forecast_items.append({
            "name": name,
            "category": cat,
            "current_month_qty": int(curr_qty),
            "projected_next_month_qty": final_forecast_qty,
            "unit": r["unit"],
            "unit_price": price,
            "projected_revenue": projected_rev,
            "growth_trend": round(((final_forecast_qty - curr_qty) / max(1, curr_qty)) * 100, 1),
            "stocking_action": f"Prepare inventory for ~{final_forecast_qty} {r['unit']} ({'+' if final_forecast_qty > curr_qty else ''}{round(((final_forecast_qty - curr_qty) / max(1, curr_qty)) * 100)}% vs last month)"
        })

    forecast_items.sort(key=lambda x: x["projected_revenue"], reverse=True)

    return {
        "target_month": next_month_name,
        "target_season": target_season,
        "total_projected_revenue": round(total_projected_revenue, 2),
        "total_projected_units": total_projected_units,
        "forecast_items": forecast_items
    }

def get_seasonal_and_festival_roadmap() -> Dict[str, Any]:
    """
    Provides multi-month forward roadmap for upcoming seasons and major Indian festivals.
    """
    today = datetime.now()
    current_year = today.year

    upcoming_festivals = []

    for fest in FESTIVAL_CALENDAR:
        # Approximate target date
        target_year = current_year if fest["month"] >= today.month else current_year + 1
        fest_date = datetime(target_year, fest["month"], fest["day"])
        days_until = (fest_date - today).days

        # Format urgency
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
