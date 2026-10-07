import json
import random
from datetime import datetime, timedelta
from database import init_db, get_connection

CATALOG_PRODUCTS = [
    # Staples
    {"name": "Aashirvaad Atta 5kg", "category": "Staples", "unit": "packet", "price": 240.0, "season": "All-Season", "trend_bias": 1.25, "aliases": ["aashirvaad 5k", "atta 5kg", "gehu aata"]},
    {"name": "Tata Salt 1kg", "category": "Staples", "unit": "packet", "price": 28.0, "season": "All-Season", "trend_bias": 1.05, "aliases": ["tata namak", "namak 1k", "tata salt"]},
    {"name": "Sugar (Loose)", "category": "Staples", "unit": "kg", "price": 45.0, "season": "Festive", "trend_bias": 0.90, "aliases": ["cheeni", "sugar", "sakkar"]},
    {"name": "Toor Dal 1kg", "category": "Staples", "unit": "kg", "price": 160.0, "season": "All-Season", "trend_bias": 1.10, "aliases": ["toor dal", "arhar dal", "tuvar dal"]},
    {"name": "Fortune Mustard Oil 1L", "category": "Staples", "unit": "bottle", "price": 155.0, "season": "Winter", "trend_bias": 1.15, "aliases": ["fortune tel", "mustard oil", "sarson tel"]},
    {"name": "India Gate Basmati Rice 1kg", "category": "Staples", "unit": "packet", "price": 130.0, "season": "Festive", "trend_bias": 1.08, "aliases": ["basmati rice", "chawal"]},
    {"name": "Besan (Gram Flour) 500g", "category": "Staples", "unit": "packet", "price": 55.0, "season": "Festive", "trend_bias": 1.12, "aliases": ["besan", "chana besan"]},
    {"name": "Amul Pure Ghee 1L", "category": "Staples", "unit": "tin", "price": 610.0, "season": "Winter", "trend_bias": 1.18, "aliases": ["amul ghee", "ghee 1l", "desi ghee"]},

    # Dairy & Morning Routine
    {"name": "Amul Taaza Milk 500ml", "category": "Dairy", "unit": "packet", "price": 27.0, "season": "All-Season", "trend_bias": 1.30, "aliases": ["amul taaza", "taaza 500", "amul doodh"]},
    {"name": "Amul Gold Milk 500ml", "category": "Dairy", "unit": "packet", "price": 33.0, "season": "All-Season", "trend_bias": 1.15, "aliases": ["amul gold", "gold 500"]},
    {"name": "Amul Masti Dahi 400g", "category": "Dairy", "unit": "cup", "price": 36.0, "season": "Summer", "trend_bias": 1.20, "aliases": ["amul dahi", "dahi", "masti dahi"]},
    {"name": "Amul Butter 100g", "category": "Dairy", "unit": "piece", "price": 58.0, "season": "All-Season", "trend_bias": 1.10, "aliases": ["amul butter", "butter 100g"]},

    # Snacks & Quick Prep (High Growth Trend)
    {"name": "Maggi 2-Minute Noodles 70g", "category": "Snacks", "unit": "packet", "price": 14.0, "season": "Monsoon", "trend_bias": 1.45, "aliases": ["maggi", "maggie", "maggi packet"]},
    {"name": "Parle-G Biscuits 100g", "category": "Snacks", "unit": "packet", "price": 10.0, "season": "All-Season", "trend_bias": 1.02, "aliases": ["parle g", "parle-g", "glucose biscuit"]},
    {"name": "Britannia Marie Gold 120g", "category": "Snacks", "unit": "packet", "price": 15.0, "season": "All-Season", "trend_bias": 1.08, "aliases": ["marie gold", "marie biscuit"]},
    {"name": "Britannia Good Day 100g", "category": "Snacks", "unit": "packet", "price": 20.0, "season": "All-Season", "trend_bias": 1.10, "aliases": ["good day", "goodday"]},
    {"name": "Lay's Magic Masala 50g", "category": "Snacks", "unit": "packet", "price": 20.0, "season": "All-Season", "trend_bias": 1.25, "aliases": ["lays blue", "lays masala"]},
    {"name": "Haldiram Aloo Bhujia 200g", "category": "Snacks", "unit": "packet", "price": 55.0, "season": "Festive", "trend_bias": 1.20, "aliases": ["aloo bhujia", "haldiram bhujia"]},

    # Beverages (Strong Seasonal Variances)
    {"name": "Brooke Bond Red Label Tea 250g", "category": "Beverages", "unit": "packet", "price": 135.0, "season": "Winter", "trend_bias": 1.10, "aliases": ["red label chai", "chai patti", "tea"]},
    {"name": "Thums Up 250ml Bottle", "category": "Beverages", "unit": "bottle", "price": 20.0, "season": "Summer", "trend_bias": 1.15, "aliases": ["thums up", "thumsup", "cold drink"]},
    {"name": "Sting Energy Drink 250ml", "category": "Beverages", "unit": "bottle", "price": 20.0, "season": "Summer", "trend_bias": 1.65, "aliases": ["sting", "energy drink"]},
    {"name": "Frooti Mango Drink 160ml", "category": "Beverages", "unit": "tetra", "price": 10.0, "season": "Summer", "trend_bias": 0.88, "aliases": ["frooti", "mango drink"]},

    # Cleaning & Hygiene
    {"name": "Surf Excel Easy Wash 500g", "category": "Cleaning", "unit": "packet", "price": 75.0, "season": "All-Season", "trend_bias": 1.12, "aliases": ["surf excel", "surf 500g", "washing powder"]},
    {"name": "Vim Dishwash Bar 155g", "category": "Cleaning", "unit": "piece", "price": 20.0, "season": "All-Season", "trend_bias": 1.05, "aliases": ["vim bar", "vim sabun"]},
    {"name": "Dettol Soap 75g", "category": "Personal Care", "unit": "piece", "price": 40.0, "season": "Monsoon", "trend_bias": 1.05, "aliases": ["dettol soap", "dettol sabun"]}
]

# Basket Templates representing real-world shopping patterns
BASKET_PATTERNS = [
    {
        "name": "Breakfast Daily",
        "time": "Morning",
        "items": [("Amul Taaza Milk 500ml", 2), ("Britannia Marie Gold 120g", 1)]
    },
    {
        "name": "Chai Time Ritual",
        "time": "Evening",
        "items": [("Brooke Bond Red Label Tea 250g", 1), ("Sugar (Loose)", 1), ("Parle-G Biscuits 100g", 2)]
    },
    {
        "name": "Evening Quick Munch",
        "time": "Evening",
        "items": [("Maggi 2-Minute Noodles 70g", 3), ("Thums Up 250ml Bottle", 2)]
    },
    {
        "name": "Youth Refreshment",
        "time": "Afternoon",
        "items": [("Sting Energy Drink 250ml", 1), ("Lay's Magic Masala 50g", 1)]
    },
    {
        "name": "Weekend Household Replenishment",
        "time": "Evening",
        "items": [("Aashirvaad Atta 5kg", 1), ("Toor Dal 1kg", 1), ("Tata Salt 1kg", 1), ("Fortune Mustard Oil 1L", 1)]
    },
    {
        "name": "Pooja & Sweet Prep",
        "time": "Morning",
        "items": [("Besan (Gram Flour) 500g", 1), ("Sugar (Loose)", 2), ("Amul Pure Ghee 1L", 1)]
    },
    {
        "name": "Kitchen Sanitation",
        "time": "Morning",
        "items": [("Surf Excel Easy Wash 500g", 1), ("Vim Dishwash Bar 155g", 2)]
    }
]

def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Insert Catalog Items
    for item in CATALOG_PRODUCTS:
        aliases_json = json.dumps(item["aliases"])
        cursor.execute("""
            INSERT OR REPLACE INTO catalog_items (name, category, standard_unit, default_price, seasonality_tag, aliases)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item["name"], item["category"], item["unit"], item["price"], item["season"], aliases_json))

    conn.commit()

    # 2. Check if transaction data already exists
    cursor.execute("SELECT COUNT(*) FROM sale_items")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("Generating 180 days (6 months) of multi-season Kirana transactions for pattern and forecast modeling...")

    today = datetime.now()
    days_to_seed = 180  # 6 months of historical depth

    item_lookup = {p["name"]: p for p in CATALOG_PRODUCTS}

    days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day_offset in range(days_to_seed, -1, -1):
        sale_dt = today - timedelta(days=day_offset)
        sale_date_str = sale_dt.strftime("%Y-%m-%d")
        month_str = sale_dt.strftime("%Y-%m")
        day_of_week = days_names[sale_dt.weekday()]
        month_int = sale_dt.month

        # Determine Season
        if month_int in [3, 4, 5, 6]:
            season_name = "Summer"
        elif month_int in [7, 8, 9]:
            season_name = "Monsoon"
        elif month_int in [10, 11]:
            season_name = "Festive"
        else:
            season_name = "Winter"

        # Time progress factor (0.0 at oldest day -> 1.0 today)
        timeline_prog = 1.0 - (day_offset / days_to_seed)

        # Base number of customer baskets per day (weekends are busier)
        is_weekend = day_of_week in ["Saturday", "Sunday"]
        num_baskets = random.randint(18, 28) if is_weekend else random.randint(12, 18)

        cursor.execute("""
            INSERT INTO sales_batches (batch_date, created_at, raw_json, items_count, total_revenue)
            VALUES (?, ?, ?, 0, 0.0)
        """, (sale_date_str, f"{sale_date_str} 22:00:00", "{}"))
        batch_id = cursor.lastrowid

        batch_rev = 0.0
        batch_items = 0

        for b_idx in range(num_baskets):
            basket_id = f"BSK-{sale_date_str}-{b_idx+1}"
            pattern = random.choice(BASKET_PATTERNS)
            time_period = pattern["time"]

            for item_name, base_qty in pattern["items"]:
                p_info = item_lookup[item_name]

                # Apply seasonal multiplier
                season_mult = 1.0
                if p_info["season"] == season_name:
                    season_mult = 1.6
                elif p_info["season"] == "Summer" and season_name == "Winter":
                    season_mult = 0.4
                elif p_info["season"] == "Winter" and season_name == "Summer":
                    season_mult = 0.6

                # Apply changing growth trend bias (Sting, Maggi growing fast; loose sugar declining)
                trend_mult = 1.0 + (p_info["trend_bias"] - 1.0) * timeline_prog

                # Skip probability based on seasonal/trend suppression
                chance = season_mult * trend_mult
                if chance < 0.6 and random.random() > chance:
                    continue

                qty = float(base_qty)
                unit_price = p_info["price"]
                line_total = round(qty * unit_price, 2)

                cursor.execute("""
                    INSERT INTO sale_items (
                        batch_id, sale_date, month_str, day_of_week, time_period,
                        basket_id, product_name, category, quantity, unit, unit_price, total_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id, sale_date_str, month_str, day_of_week, time_period,
                    basket_id, item_name, p_info["category"], qty, p_info["unit"], unit_price, line_total
                ))

                batch_rev += line_total
                batch_items += 1

        cursor.execute("""
            UPDATE sales_batches
            SET items_count = ?, total_revenue = ?
            WHERE id = ?
        """, (batch_items, round(batch_rev, 2), batch_id))

    conn.commit()
    conn.close()
    print("Historical transaction patterns & trend data seeded successfully!")

if __name__ == "__main__":
    seed_database()
