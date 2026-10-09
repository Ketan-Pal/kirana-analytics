import json
from datetime import datetime
from typing import Dict, Any, List
from database import get_connection
from catalog_matcher import match_catalog_item, auto_register_catalog_item
from logging_config import get_logger

logger = get_logger("ingestion")

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def ingest_gemini_sales_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingests structured JSON output transcribed from the notepad columns:
    [sale no.] [time] [products quantity and size] [total amount] [weather] [festival]
    into Supabase PostgreSQL.
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
    try:
        with conn.cursor() as cur:
            # 1. Create sales batch in Supabase
            cur.execute("""
                INSERT INTO sales_batches (batch_date, weather, festival, raw_json, items_count, total_revenue)
                VALUES (%s, %s, %s, %s::jsonb, 0, 0.0)
                RETURNING id;
            """, (raw_date, day_weather, day_festival, json.dumps(payload)))
            batch_id = cur.fetchone()["id"]

            total_batch_revenue = 0.0
            total_items_count = 0
            matched_count = 0
            new_count = 0
            processed_sales = []

            for s_entry in sales_entries:
                sale_no = int(s_entry.get("sale_no") or 1)
                sale_time = str(s_entry.get("time") or "")
                time_period = str(s_entry.get("time_period") or "Evening")
                if time_period not in ["Morning", "Afternoon", "Evening", "Night"]:
                    time_period = "Evening"

                sale_weather = str(s_entry.get("weather") or day_weather)
                sale_festival = str(s_entry.get("festival") or day_festival)
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
                        if line_total == 0.0 and float(matched["default_price"]) > 0:
                            unit_price = float(matched["default_price"])
                            line_total = round(qty * unit_price, 2)
                    else:
                        new_count += 1
                        new_item = auto_register_catalog_item(raw_text, std_name, category, unit_price, unit)
                        final_name = new_item["name"]
                        final_cat = new_item["category"]
                        final_unit = new_item["standard_unit"]
                        if line_total == 0.0 and float(new_item["default_price"]) > 0:
                            unit_price = float(new_item["default_price"])
                            line_total = round(qty * unit_price, 2)

                    total_batch_revenue += line_total
                    total_items_count += 1

                    cur.execute("""
                        INSERT INTO sale_items (
                            batch_id, sale_no, sale_date, sale_time, time_period,
                            month_str, day_of_week, weather, festival,
                            basket_id, product_name, category, quantity, unit, pack_size,
                            unit_price, total_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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

            cur.execute("""
                UPDATE sales_batches
                SET items_count = %s, total_revenue = %s
                WHERE id = %s;
            """, (total_items_count, round(total_batch_revenue, 2), batch_id))

        conn.commit()

        # Auto-enrich analytics cache with Gemini on ingestion
        try:
            from gemini_enricher import enrich_analytics_with_gemini
            enrich_analytics_with_gemini(force_refresh=True)
        except Exception as e:
            logger.warning(f"AI enrichment trigger failed: {e}")

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
    finally:
        conn.close()
