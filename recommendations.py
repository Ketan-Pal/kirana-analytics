import itertools
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_connection

def get_reorder_recommendations() -> Dict[str, Any]:
    """
    7-Eleven Tanpin Kanri Replenishment Logic:
    Calculates dynamic safety stock and suggested reorder quantities.
    Generates a WhatsApp-ready order list for distributors.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate daily sales run-rate over the last 7 days
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT 
            i.id,
            i.sku,
            i.name,
            i.category,
            i.stock_qty,
            i.min_safety_stock,
            i.lead_time_days,
            i.unit,
            i.cost_price,
            COALESCE(SUM(s.quantity), 0.0) as units_sold_7d
        FROM items i
        LEFT JOIN sale_items s ON i.id = s.item_id AND s.sale_date >= ?
        GROUP BY i.id
    """, (cutoff_date,))
    items = cursor.fetchall()
    conn.close()

    reorder_list = []
    healthy_list = []

    for row in items:
        units_sold = row["units_sold_7d"]
        daily_demand = units_sold / 7.0 if units_sold > 0 else 0.1
        lead_time = max(1, row["lead_time_days"])
        current_stock = row["stock_qty"]
        min_safety = row["min_safety_stock"]

        # Dynamic safety threshold
        safety_stock_threshold = max(min_safety, round(daily_demand * lead_time * 1.5, 1))

        # Reorder trigger
        if current_stock <= safety_stock_threshold:
            # Target stock is enough for (lead_time + 5 days) of sales
            target_stock = round(daily_demand * (lead_time + 5))
            suggested_qty = max(5, int(target_stock - current_stock))
            estimated_cost = round(suggested_qty * row["cost_price"], 2)
            
            urgency = "HIGH (Stockout Risk)" if current_stock <= (daily_demand * lead_time) else "MEDIUM"

            reorder_list.append({
                "item_id": row["id"],
                "sku": row["sku"],
                "name": row["name"],
                "category": row["category"],
                "current_stock": current_stock,
                "daily_demand": round(daily_demand, 1),
                "safety_threshold": safety_stock_threshold,
                "suggested_order_qty": suggested_qty,
                "unit": row["unit"],
                "estimated_cost": estimated_cost,
                "urgency": urgency
            })
        else:
            healthy_list.append({
                "name": row["name"],
                "current_stock": current_stock,
                "daily_demand": round(daily_demand, 1)
            })

    # Sort reorders by urgency
    reorder_list.sort(key=lambda x: (x["urgency"] == "HIGH (Stockout Risk)", x["suggested_order_qty"]), reverse=True)

    # Format distributor WhatsApp message
    today_formatted = datetime.now().strftime("%d-%b-%Y")
    order_lines = [f"*Kirana Store Order - {today_formatted}*", "Namaste! Please deliver the following items today:"]
    for idx, r in enumerate(reorder_list, 1):
        order_lines.append(f"{idx}. {r['name']} : {r['suggested_order_qty']} {r['unit']}")
    order_lines.append("\nPlease confirm delivery time. Thank you!")
    whatsapp_text = "\n".join(order_lines)

    return {
        "needs_reorder_count": len(reorder_list),
        "reorder_items": reorder_list,
        "whatsapp_order_text": whatsapp_text,
        "total_estimated_reorder_value": sum(r["estimated_cost"] for r in reorder_list)
    }

def get_basket_cross_sell_recommendations(min_support_count: int = 3) -> List[Dict[str, Any]]:
    """
    Market Basket Association Analysis:
    Identifies items bought together and converts them into:
    - Shelf placement recommendations
    - Combo bundle promotions
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all baskets and their line items
    cursor.execute("""
        SELECT basket_id, standardized_name
        FROM sale_items
        WHERE basket_id IS NOT NULL AND basket_id != ''
        GROUP BY basket_id, standardized_name
    """)
    rows = cursor.fetchall()
    conn.close()

    basket_map = defaultdict(list)
    item_counts = defaultdict(int)

    for r in rows:
        b_id = r["basket_id"]
        item = r["standardized_name"]
        basket_map[b_id].append(item)
        item_counts[item] += 1

    total_baskets = len(basket_map)
    if total_baskets < 5:
        return []

    # Count co-occurrences
    pair_counts = defaultdict(int)
    for items in basket_map.values():
        if len(items) >= 2:
            for item_a, item_b in itertools.combinations(sorted(items), 2):
                pair_counts[(item_a, item_b)] += 1

    recommendations = []

    for (item_a, item_b), count in pair_counts.items():
        if count >= min_support_count:
            # Confidence A -> B
            conf_a_b = count / item_counts[item_a]
            conf_b_a = count / item_counts[item_b]
            
            # Lift = P(A & B) / (P(A) * P(B))
            lift = (count / total_baskets) / ((item_counts[item_a] / total_baskets) * (item_counts[item_b] / total_baskets))

            if lift > 1.2:
                recommendations.append({
                    "item_a": item_a,
                    "item_b": item_b,
                    "co_occurrence_count": count,
                    "confidence_pct": round(max(conf_a_b, conf_b_a) * 100, 1),
                    "lift": round(lift, 2),
                    "shelf_advice": f"Place '{item_b}' directly adjacent to '{item_a}'. Customers buy them together {round(max(conf_a_b, conf_b_a) * 100)}% of the time.",
                    "combo_promo": f"Launch a combo promo: '{item_a} + {item_b}' with ₹5 instant discount to maximize basket value."
                })

    recommendations.sort(key=lambda x: (x["lift"], x["co_occurrence_count"]), reverse=True)
    return recommendations[:8]

def get_dead_stock_warnings(days_threshold: int = 7) -> List[Dict[str, Any]]:
    """
    Identifies Class C dead inventory tying up store working capital.
    Provides actionable markdown or clearance bundles.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT 
            i.id,
            i.name,
            i.category,
            i.stock_qty,
            i.sale_price,
            i.cost_price,
            COALESCE(SUM(s.quantity), 0) as recent_sales
        FROM items i
        LEFT JOIN sale_items s ON i.id = s.item_id AND s.sale_date >= ?
        WHERE i.stock_qty > 0
        GROUP BY i.id
        HAVING recent_sales <= 1
        ORDER BY (i.stock_qty * i.cost_price) DESC
    """, (cutoff_date,))
    rows = cursor.fetchall()
    conn.close()

    warnings = []
    for r in rows:
        tied_capital = round(r["stock_qty"] * r["cost_price"], 2)
        if tied_capital > 500 or r["stock_qty"] >= 5:
            warnings.append({
                "name": r["name"],
                "category": r["category"],
                "current_stock": r["stock_qty"],
                "tied_capital": tied_capital,
                "recent_sales": r["recent_sales"],
                "action_plan": f"Clearance Alert: ₹{tied_capital} tied up in {r['stock_qty']} units. Offer 10% markdown or offer as a bonus gift with 5kg Atta/Oil."
            })

    return warnings
