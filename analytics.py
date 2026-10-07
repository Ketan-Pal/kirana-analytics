import itertools
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_connection

def get_basket_co_purchases(min_pairs: int = 4) -> List[Dict[str, Any]]:
    """Analyzes customer basket combinations from Supabase PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT basket_id, product_name
                FROM sale_items
                GROUP BY basket_id, product_name;
            """)
            rows = cur.fetchall()
    finally:
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
    """Weekday vs Weekend shopping shifts."""
    conn = get_connection()
    try:
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    day_of_week,
                    COUNT(DISTINCT basket_id) as total_baskets,
                    COALESCE(SUM(total_amount), 0.0) as total_revenue,
                    COALESCE(SUM(quantity), 0.0) as total_units
                FROM sale_items
                GROUP BY day_of_week;
            """)
            rows = {r["day_of_week"]: dict(r) for r in cur.fetchall()}

            top_items_by_day = {}
            for d in days_order:
                cur.execute("""
                    SELECT product_name, SUM(quantity) as qty
                    FROM sale_items
                    WHERE day_of_week = %s
                    GROUP BY product_name
                    ORDER BY qty DESC
                    LIMIT 2;
                """, (d,))
                top_items_by_day[d] = [r["product_name"] for r in cur.fetchall()]
    finally:
        conn.close()

    result = []
    for d in days_order:
        data = rows.get(d, {"total_baskets": 0, "total_revenue": 0.0, "total_units": 0.0})
        baskets = max(1, data["total_baskets"])
        revenue = float(data["total_revenue"])
        avg_basket = round(revenue / baskets, 1)

        is_weekend = d in ["Saturday", "Sunday"]
        pattern_theme = "Weekend Surge (Family Snacking & Bulk Purchases)" if is_weekend else "Weekday Replenishment (Daily Essentials)"

        result.append({
            "day": d,
            "total_baskets": data["total_baskets"],
            "total_revenue": round(revenue, 2),
            "avg_basket_value": avg_basket,
            "pattern_theme": pattern_theme,
            "top_drivers": top_items_by_day.get(d, [])
        })

    return result

def get_weather_impact_analysis() -> List[Dict[str, Any]]:
    """Analyzes how weather conditions directly influence item demand from Supabase."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT weather, COUNT(DISTINCT sale_date) as days_count
                FROM sale_items
                GROUP BY weather;
            """)
            weather_days = {r["weather"]: max(1, r["days_count"]) for r in cur.fetchall()}

            cur.execute("""
                SELECT weather, product_name, category, SUM(quantity) as total_qty
                FROM sale_items
                GROUP BY weather, product_name, category
                ORDER BY total_qty DESC;
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    weather_grouped = defaultdict(list)
    for r in rows:
        w = r["weather"]
        days = weather_days.get(w, 1)
        daily_rate = round(float(r["total_qty"]) / days, 1)
        weather_grouped[w].append({
            "product_name": r["product_name"],
            "category": r["category"],
            "avg_daily_qty": daily_rate
        })

    insights = []
    for w, items in weather_grouped.items():
        if w in ["Rainy", "Hot", "Cold", "Sunny"]:
            top_items = sorted(items, key=lambda x: x["avg_daily_qty"], reverse=True)[:3]
            theme = ""
            if w == "Rainy":
                theme = "Rain Spikes: High demand for hot tea, instant comfort foods (Maggi), and frying staples."
            elif w == "Hot":
                theme = "Heat Spikes: High demand for chilled soft drinks, dahi, and energy beverages."
            elif w == "Cold":
                theme = "Winter Spikes: High demand for ghee, mustard oil, and morning hot beverages."
            else:
                theme = "Sunny / Normal: Balanced daily household replenishment."

            insights.append({
                "weather": w,
                "days_observed": weather_days.get(w, 0),
                "behavior_theme": theme,
                "top_products": top_items
            })

    return insights

def get_time_of_day_patterns() -> List[Dict[str, Any]]:
    """Buying shifts across Morning, Afternoon, and Evening."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    time_period,
                    COUNT(DISTINCT basket_id) as baskets,
                    COALESCE(SUM(total_amount), 0.0) as revenue
                FROM sale_items
                GROUP BY time_period
                ORDER BY revenue DESC;
            """)
            rows = [dict(r) for r in cur.fetchall()]

            for r in rows:
                cur.execute("""
                    SELECT category, SUM(quantity) as qty
                    FROM sale_items
                    WHERE time_period = %s
                    GROUP BY category
                    ORDER BY qty DESC
                    LIMIT 1;
                """, (r["time_period"],))
                dominant = cur.fetchone()
                r["dominant_category"] = dominant["category"] if dominant else "General"
                r["revenue"] = float(r["revenue"])
    finally:
        conn.close()

    return rows

def get_changing_trend_patterns() -> Dict[str, Any]:
    """Momentum detection (recent 30d vs prior 30d) in PostgreSQL."""
    conn = get_connection()
    try:
        today = datetime.now()
        d_recent_end = today.strftime("%Y-%m-%d")
        d_recent_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        d_prior_end = (today - timedelta(days=31)).strftime("%Y-%m-%d")
        d_prior_start = (today - timedelta(days=60)).strftime("%Y-%m-%d")

        with conn.cursor() as cur:
            cur.execute("""
                SELECT product_name, category, SUM(quantity) as recent_qty, SUM(total_amount) as recent_rev
                FROM sale_items
                WHERE sale_date BETWEEN %s AND %s
                GROUP BY product_name, category;
            """, (d_recent_start, d_recent_end))
            recent_map = {r["product_name"]: dict(r) for r in cur.fetchall()}

            cur.execute("""
                SELECT product_name, category, SUM(quantity) as prior_qty, SUM(total_amount) as prior_rev
                FROM sale_items
                WHERE sale_date BETWEEN %s AND %s
                GROUP BY product_name, category;
            """, (d_prior_start, d_prior_end))
            prior_map = {r["product_name"]: dict(r) for r in cur.fetchall()}
    finally:
        conn.close()

    growth_analysis = []
    all_products = set(recent_map.keys()).union(set(prior_map.keys()))

    for p in all_products:
        r_qty = float(recent_map.get(p, {}).get("recent_qty") or 0.0)
        p_qty = float(prior_map.get(p, {}).get("prior_qty") or 0.0)
        category = recent_map.get(p, {}).get("category") or prior_map.get(p, {}).get("category") or "Other"

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

    surging_items = sorted([g for g in growth_analysis if g["is_surging"]], key=lambda x: x["growth_pct"], reverse=True)
    declining_items = sorted([g for g in growth_analysis if g["is_declining"]], key=lambda x: x["growth_pct"])

    return {
        "surging_products": surging_items[:6],
        "declining_products": declining_items[:6],
        "all_product_trends": sorted(growth_analysis, key=lambda x: x["growth_pct"], reverse=True)
    }

def get_historical_monthly_summary() -> List[Dict[str, Any]]:
    """Monthly progression from PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    month_str,
                    COUNT(DISTINCT basket_id) as total_baskets,
                    COALESCE(SUM(total_amount), 0.0) as revenue,
                    COALESCE(SUM(quantity), 0.0) as total_units
                FROM sale_items
                GROUP BY month_str
                ORDER BY month_str ASC;
            """)
            rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    for r in rows:
        baskets = max(1, r["total_baskets"])
        revenue = float(r["revenue"])
        r["avg_basket_value"] = round(revenue / baskets, 1)
        r["revenue"] = round(revenue, 2)
        r["total_units"] = int(float(r["total_units"]))

    return rows
