import json
from datetime import datetime
from typing import Dict, Any, List
from database import get_connection
from catalog_matcher import match_catalog_item, auto_register_catalog_item

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def ingest_gemini_sales_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingests the Gemini JSON output from daily sales notepad notes into the pattern analysis store.
    """
    raw_date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    transactions = payload.get("transactions", [])

    if not transactions:
        raise ValueError("No transaction items found in the payload.")

    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
        raw_date = dt.strftime("%Y-%m-%d")

    month_str = dt.strftime("%Y-%m")
    day_of_week = DAYS_OF_WEEK[dt.weekday()]

    conn = get_connection()
    cursor = conn.cursor()

    # Create batch record
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO sales_batches (batch_date, created_at, raw_json, items_count, total_revenue)
        VALUES (?, ?, ?, ?, 0.0)
    """, (raw_date, now_timestamp, json.dumps(payload), len(transactions)))
    batch_id = cursor.lastrowid

    total_batch_revenue = 0.0
    matched_count = 0
    new_count = 0
    processed_items = []

    # Assign basket IDs (batch items grouped by 3 or customer note)
    for idx, item_data in enumerate(transactions, 1):
        raw_text = item_data.get("raw_text") or item_data.get("standardized_name", "Unknown Item")
        std_name = item_data.get("standardized_name") or raw_text
        category = item_data.get("category") or "Other"
        qty = float(item_data.get("quantity") or 1.0)
        unit = item_data.get("unit") or "packet"
        unit_price = float(item_data.get("unit_price") or 0.0)
        total_amount = float(item_data.get("total_amount") or (qty * unit_price))
        customer_note = item_data.get("customer_note")

        # Match or auto-register
        matched = match_catalog_item(raw_text, std_name)
        if matched:
            matched_count += 1
            final_name = matched["name"]
            final_cat = matched["category"]
            final_unit = matched["standard_unit"]
            if total_amount == 0.0:
                unit_price = matched["default_price"]
                total_amount = round(qty * unit_price, 2)
        else:
            new_count += 1
            new_item = auto_register_catalog_item(raw_text, std_name, category, unit_price, unit)
            final_name = new_item["name"]
            final_cat = new_item["category"]
            final_unit = new_item["standard_unit"]
            if total_amount == 0.0:
                unit_price = new_item["default_price"]
                total_amount = round(qty * unit_price, 2)

        total_batch_revenue += total_amount

        # Basket grouping for pattern mining
        basket_id = f"BSK-{raw_date}-{customer_note}" if customer_note else f"BSK-{raw_date}-{idx // 3 + 1}"

        cursor.execute("""
            INSERT INTO sale_items (
                batch_id, sale_date, month_str, day_of_week, time_period,
                basket_id, product_name, category, quantity, unit, unit_price, total_amount
            ) VALUES (?, ?, ?, ?, 'Evening', ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, raw_date, month_str, day_of_week,
            basket_id, final_name, final_cat, qty, final_unit, unit_price, total_amount
        ))

        processed_items.append({
            "name": final_name,
            "category": final_cat,
            "quantity": qty,
            "total_amount": total_amount
        })

    cursor.execute("""
        UPDATE sales_batches
        SET total_revenue = ?
        WHERE id = ?
    """, (round(total_batch_revenue, 2), batch_id))

    conn.commit()
    conn.close()

    return {
        "batch_id": batch_id,
        "date": raw_date,
        "items_processed": len(transactions),
        "matched_items": matched_count,
        "new_items_added": new_count,
        "total_revenue": round(total_batch_revenue, 2),
        "processed_items": processed_items
    }
