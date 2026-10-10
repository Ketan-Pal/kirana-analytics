import pytest
from ingestion import ingest_gemini_sales_json
from catalog_matcher import match_catalog_item, clean_text

def test_clean_text_helper():
    assert clean_text("Amul Taaza (500ml)!") == "amul taaza 500ml"
    assert clean_text("  TATA   SALT  ") == "tata salt"
    assert clean_text("") == ""

def test_match_catalog_item_known_alias():
    matched = match_catalog_item("amul taaza 500")
    assert matched is not None
    assert "Amul Taaza Milk 500ml" in matched["name"]

def test_ingest_empty_payload_fails():
    with pytest.raises(ValueError):
        ingest_gemini_sales_json({"sales": []})

def test_ingest_valid_sample_sale():
    sample_payload = {
        "date": "2026-10-09",
        "day_weather": "Rainy",
        "day_festival": "None",
        "sales": [
            {
                "sale_no": 9991,
                "time": "08:15 AM",
                "time_period": "Morning",
                "bill_total": 42.0,
                "weather": "Rainy",
                "festival": "None",
                "items": [
                    {
                        "raw_text": "1 amul taaza 500",
                        "standardized_name": "Amul Taaza Milk 500ml",
                        "category": "Dairy",
                        "quantity": 1,
                        "unit": "packet",
                        "pack_size": "500ml",
                        "unit_price": 27.0,
                        "line_total": 27.0
                    },
                    {
                        "raw_text": "1 marie 120g",
                        "standardized_name": "Britannia Marie Gold 120g",
                        "category": "Snacks",
                        "quantity": 1,
                        "unit": "packet",
                        "pack_size": "120g",
                        "unit_price": 15.0,
                        "line_total": 15.0
                    }
                ]
            }
        ]
    }
    try:
        result = ingest_gemini_sales_json(sample_payload)
        assert result["batch_id"] is not None
        assert result["sales_recorded"] == 1
        assert result["total_items_processed"] == 2
    finally:
        from database import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM sale_items WHERE sale_no = 9991;")
            cur.execute("DELETE FROM sales_batches WHERE raw_json->'sales'->0->>'sale_no' = '9991';")
            cur.execute("DELETE FROM ai_insights_cache WHERE cache_key = 'latest_enrichment';")
