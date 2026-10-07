import itertools
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_connection

def get_basket_co_purchases(min_pairs: int = 4) -> List[Dict[str, Any]]:
    """
    Analyzes which items are consistently bought together in customer bills.
    Calculates co-occurrence count, confidence, and cross-sell lift.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT basket_id, product_name
        FROM sale_items
        GROUP BY basket_id, product_name
    """)
    rows = cursor.fetchall()
    conn.close()

    baskets = defaultdict(set)
    item_freq = defaultdict(int)

    for r in rows:
        baskets[r["basket_id"]].add(r["product_name"])
        item_freq[r["product_name"]] += 1

    total_baskets = len(baskets)
    if total_baskets == 0:
        return []

    pair_counts = defaultdict(int)
    for items in baskets.values():
        if len(items) >= 2:
            for item_a, item_b in itertools.combinations(sorted(items), 2):
                pair_counts[(item_a, item_b)] += 1

    results = []
    for (item_a, item_b), count in pair_counts.items():
        if count >= min_pairs:
            conf_a_b = count / item_freq[item_a]
            conf_b_a = count / item_freq[item_b]
            max_conf = max(conf_a_b, conf_b_a)

            # Lift = P(A & B) / (P(A) * P(B))
            lift = (count / total_baskets) / ((item_freq[item_a] / total_baskets) * (item_freq[item_b] / total_baskets))

            results.append({
                "item_a": item_a,
                "item_b": item_b,
                "times_bought_together": count,
                "confidence_pct": round(max_conf * 100, 1),
                "lift": round(lift, 2),
                "insight": f"Customers buying '{item_a}' also buy '{item_b}' {round(max_conf * 100)}% of the time."
            })

    results.sort(key=lambda x: (x["lift"], x["times_bought_together"]), reverse=True)
    return results[:10]

def get_day_of_week_patterns() -> List[Dict[str, Any]]:
    """
    Identifies customer buying patterns across days of the week:
    Shows how demand shifts between Weekdays (staples/essentials) and Weekends (treats/parties/bulk).
    """
    conn = get_connection()
    cursor = conn.cursor()

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    cursor.execute("""
        SELECT 
            day_of_week,
            COUNT(DISTINCT basket_id) as total_baskets,
            SUM(total_amount) as total_revenue,
            SUM(quantity) as total_units
        FROM sale_items
        GROUP BY day_of_week
    """)
    rows = {r["day_of_week"]: dict(r) for r in cursor.fetchall()}

    # Top selling product by day
    top_items_by_day = {}
    for d in days_order:
        cursor.execute("""
            SELECT product_name, SUM(quantity) as qty
            FROM sale_items
            WHERE day_of_week = ?
            GROUP BY product_name
            ORDER BY qty DESC
            LIMIT 2
        """, (d,))
        top_items_by_day[d] = [r["product_name"] for r in cursor.fetchall()]

    conn.close()

    result = []
    for d in days_order:
        data = rows.get(d, {"total_baskets": 0, "total_revenue": 0.0, "total_units": 0})
        baskets = max(1, data["total_baskets"])
        avg_basket = round(data["total_revenue"] / baskets, 1)

        is_weekend = d in ["Saturday", "Sunday"]
        pattern_theme = "Weekend Surge (Family Snacking & Bulk Purchases)" if is_weekend else "Weekday Replenishment (Daily Essentials)"

        result.append({
            "day": d,
            "total_baskets": data["total_baskets"],
            "total_revenue": round(data["total_revenue"], 2),
            "avg_basket_value": avg_basket,
            "pattern_theme": pattern_theme,
            "top_drivers": top_items_by_day.get(d, [])
        })

    return result

def get_time_of_day_patterns() -> List[Dict[str, Any]]:
    """Buying shifts across Morning, Afternoon, and Evening."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            time_period,
            COUNT(DISTINCT basket_id) as baskets,
            SUM(total_amount) as revenue
        FROM sale_items
        GROUP BY time_period
        ORDER BY revenue DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]

    # Find dominant categories per period
    for r in rows:
        cursor.execute("""
            SELECT category, SUM(quantity) as qty
            FROM sale_items
            WHERE time_period = ?
            GROUP BY category
            ORDER BY qty DESC
            LIMIT 1
        """, (r["time_period"],))
        dominant = cursor.fetchone()
        r["dominant_category"] = dominant["category"] if dominant else "General"

    conn.close()
    return rows

def get_changing_trend_patterns() -> Dict[str, Any]:
    """
    Detects changing customer preferences by comparing the most recent 30 days
    against the previous 30-day window (Period-over-Period Momentum).
    Flags:
    - Surging Products (Fastest growing demand)
    - Declining Products (Fading demand)
    - Shifting Categories
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now()
    d_recent_end = today.strftime("%Y-%m-%d")
    d_recent_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    d_prior_end = (today - timedelta(days=31)).strftime("%Y-%m-%d")
    d_prior_start = (today - timedelta(days=60)).strftime("%Y-%m-%d")

    # Recent 30 days sales
    cursor.execute("""
        SELECT product_name, category, SUM(quantity) as recent_qty, SUM(total_amount) as recent_rev
        FROM sale_items
        WHERE sale_date BETWEEN ? AND ?
        GROUP BY product_name
    """, (d_recent_start, d_recent_end))
    recent_map = {r["product_name"]: dict(r) for r in cursor.fetchall()}

    # Prior 30 days sales
    cursor.execute("""
        SELECT product_name, category, SUM(quantity) as prior_qty, SUM(total_amount) as prior_rev
        FROM sale_items
        WHERE sale_date BETWEEN ? AND ?
        GROUP BY product_name
    """, (d_prior_start, d_prior_end))
    prior_map = {r["product_name"]: dict(r) for r in cursor.fetchall()}

    conn.close()

    growth_analysis = []
    all_products = set(recent_map.keys()).union(set(prior_map.keys()))

    for p in all_products:
        r_qty = recent_map.get(p, {}).get("recent_qty", 0.0)
        p_qty = prior_map.get(p, {}).get("prior_qty", 0.0)
        category = recent_map.get(p, {}).get("category") or prior_map.get(p, {}).get("category") or "Other"

        # Calculate momentum percentage
        if p_qty > 0:
            growth_pct = round(((r_qty - p_qty) / p_qty) * 100, 1)
        else:
            growth_pct = 100.0 if r_qty > 0 else 0.0

        growth_analysis.append({
            "product_name": p,
            "category": category,
            "recent_30d_qty": round(r_qty, 1),
            "prior_30d_qty": round(p_qty, 1),
            "growth_pct": growth_pct,
            "is_surging": growth_pct >= 15.0,
            "is_declining": growth_pct <= -10.0
        })

    # Sort
    surging_items = sorted([g for g in growth_analysis if g["is_surging"]], key=lambda x: x["growth_pct"], reverse=True)
    declining_items = sorted([g for g in growth_analysis if g["is_declining"]], key=lambda x: x["growth_pct"])

    return {
        "surging_products": surging_items[:6],
        "declining_products": declining_items[:6],
        "all_product_trends": sorted(growth_analysis, key=lambda x: x["growth_pct"], reverse=True)
    }

def get_historical_monthly_summary() -> List[Dict[str, Any]]:
    """Monthly progression of revenue, volume, and basket size over past data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            month_str,
            COUNT(DISTINCT basket_id) as total_baskets,
            SUM(total_amount) as revenue,
            SUM(quantity) as total_units
        FROM sale_items
        GROUP BY month_str
        ORDER BY month_str ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        baskets = max(1, r["total_baskets"])
        r["avg_basket_value"] = round(r["revenue"] / baskets, 1)
        r["revenue"] = round(r["revenue"], 2)

    return rows
