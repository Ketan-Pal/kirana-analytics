import json
from datetime import datetime
from typing import Dict, Any, List
from database import get_connection
from catalog_matcher import match_catalog_item, auto_register_catalog_item

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def ingest_gemini_sales_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingests structured JSON output transcribed from the notepad columns:
    [sale no.] [time] [products quantity and size] [total amount] [weather] [festival]
    """
    raw_date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    day_weather = payload.get("day_weather") or "Normal"
    day_festival = payload.get("day_festival") or "None"

    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
        raw_date = dt.strftime("%Y-%m-%d")

    month_str = dt.strftime("%Y-%m")
    day_of_week = DAYS_OF_WEEK[dt.weekday()]

    sales_entries = payload.get("sales", [])

    # Backward compatibility with flat 'transactions' structure
    if not sales_entries and "transactions" in payload:
        sales_entries = [
            {
                "sale_no": idx + 1,
                "time": "12:00 PM",
                "time_period": "Evening",
                "bill_total": float(t.get("total_amount") or 0.0),
                "weather": day_weather,
                "festival": day_festival,
                "items": [t]
            }
            for idx, t in enumerate(payload["transactions"])
        ]

    if not sales_entries:
        raise ValueError("No sales entries found in the payload.")

    conn = get_connection()
    cursor = conn.cursor()

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO sales_batches (batch_date, weather, festival, created_at, raw_json, items_count, total_revenue)
        VALUES (?, ?, ?, ?, ?, 0, 0.0)
    """, (raw_date, day_weather, day_festival, now_timestamp, json.dumps(payload)))
    batch_id = cursor.lastrowid

    total_batch_revenue = 0.0
    total_items_count = 0
    matched_count = 0
    new_count = 0
    processed_sales = []

    for s_entry in sales_entries:
        sale_no = s_entry.get("sale_no", 1)
        sale_time = s_entry.get("time", "")
        time_period = s_entry.get("time_period") or "Evening"
        sale_weather = s_entry.get("weather") or day_weather
        sale_festival = s_entry.get("festival") or day_festival
        bill_total = float(s_entry.get("bill_total") or 0.0)
        items = s_entry.get("items", [])

        basket_id = f"BSK-{raw_date}-{sale_no}"

        for it in items:
            raw_text = it.get("raw_text") or it.get("standardized_name", "Unknown Item")
            std_name = it.get("standardized_name") or raw_text
            category = it.get("category") or "Other"
            qty = float(it.get("quantity") or 1.0)
            unit = it.get("unit") or "packet"
            pack_size = it.get("pack_size") or "Standard"
            unit_price = float(it.get("unit_price") or 0.0)
            line_total = float(it.get("line_total") or it.get("total_amount") or (qty * unit_price))

            matched = match_catalog_item(raw_text, std_name)
            if matched:
                matched_count += 1
                final_name = matched["name"]
                final_cat = matched["category"]
                final_unit = matched["standard_unit"]
                if line_total == 0.0 and matched["default_price"] > 0:
                    unit_price = matched["default_price"]
                    line_total = round(qty * unit_price, 2)
            else:
                new_count += 1
                new_item = auto_register_catalog_item(raw_text, std_name, category, unit_price, unit)
                final_name = new_item["name"]
                final_cat = new_item["category"]
                final_unit = new_item["standard_unit"]
                if line_total == 0.0 and new_item["default_price"] > 0:
                    unit_price = new_item["default_price"]
                    line_total = round(qty * unit_price, 2)

            total_batch_revenue += line_total
            total_items_count += 1

            cursor.execute("""
                INSERT INTO sale_items (
                    batch_id, sale_no, sale_date, sale_time, time_period,
                    month_str, day_of_week, weather, festival,
                    basket_id, product_name, category, quantity, unit, pack_size,
                    unit_price, total_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id, sale_no, raw_date, sale_time, time_period,
                month_str, day_of_week, sale_weather, sale_festival,
                basket_id, final_name, final_cat, qty, final_unit, pack_size,
                unit_price, line_total
            ))

        processed_sales.append({
            "sale_no": sale_no,
            "time": sale_time,
            "weather": sale_weather,
            "festival": sale_festival,
            "items_count": len(items)
        })

    cursor.execute("""
        UPDATE sales_batches
        SET items_count = ?, total_revenue = ?
        WHERE id = ?
    """, (total_items_count, round(total_batch_revenue, 2), batch_id))

    conn.commit()
    conn.close()

    return {
        "batch_id": batch_id,
        "date": raw_date,
        "weather": day_weather,
        "festival": day_festival,
        "sales_recorded": len(sales_entries),
        "total_items_processed": total_items_count,
        "matched_skus": matched_count,
        "new_skus": new_count,
        "total_revenue": round(total_batch_revenue, 2),
        "sales": processed_sales
    }
