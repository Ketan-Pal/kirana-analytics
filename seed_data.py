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

    # Beverages (Strong Seasonal & Weather Variances)
    {"name": "Brooke Bond Red Label Tea 250g", "category": "Beverages", "unit": "packet", "price": 135.0, "season": "Winter", "trend_bias": 1.10, "aliases": ["red label chai", "chai patti", "tea"]},
    {"name": "Thums Up 250ml Bottle", "category": "Beverages", "unit": "bottle", "price": 20.0, "season": "Summer", "trend_bias": 1.15, "aliases": ["thums up", "thumsup", "cold drink"]},
    {"name": "Sting Energy Drink 250ml", "category": "Beverages", "unit": "bottle", "price": 20.0, "season": "Summer", "trend_bias": 1.65, "aliases": ["sting", "energy drink"]},
    {"name": "Frooti Mango Drink 160ml", "category": "Beverages", "unit": "tetra", "price": 10.0, "season": "Summer", "trend_bias": 0.88, "aliases": ["frooti", "mango drink"]},

    # Cleaning & Hygiene
    {"name": "Surf Excel Easy Wash 500g", "category": "Cleaning", "unit": "packet", "price": 75.0, "season": "All-Season", "trend_bias": 1.12, "aliases": ["surf excel", "surf 500g", "washing powder"]},
    {"name": "Vim Dishwash Bar 155g", "category": "Cleaning", "unit": "piece", "price": 20.0, "season": "All-Season", "trend_bias": 1.05, "aliases": ["vim bar", "vim sabun"]},
    {"name": "Dettol Soap 75g", "category": "Personal Care", "unit": "piece", "price": 40.0, "season": "Monsoon", "trend_bias": 1.05, "aliases": ["dettol soap", "dettol sabun"]}
]

BASKET_PATTERNS = [
    {
        "name": "Breakfast Daily",
        "time": "08:15 AM",
        "time_period": "Morning",
        "items": [("Amul Taaza Milk 500ml", 2, "500ml"), ("Britannia Marie Gold 120g", 1, "120g")]
    },
    {
        "name": "Chai Time Ritual",
        "time": "05:30 PM",
        "time_period": "Evening",
        "items": [("Brooke Bond Red Label Tea 250g", 1, "250g"), ("Sugar (Loose)", 1, "1kg"), ("Parle-G Biscuits 100g", 2, "100g")]
    },
    {
        "name": "Evening Quick Munch",
        "time": "07:10 PM",
        "time_period": "Evening",
        "items": [("Maggi 2-Minute Noodles 70g", 3, "70g"), ("Thums Up 250ml Bottle", 2, "250ml")]
    },
    {
        "name": "Youth Refreshment",
        "time": "03:45 PM",
        "time_period": "Afternoon",
        "items": [("Sting Energy Drink 250ml", 1, "250ml"), ("Lay's Magic Masala 50g", 1, "50g")]
    },
    {
        "name": "Weekend Household Replenishment",
        "time": "11:20 AM",
        "time_period": "Morning",
        "items": [("Aashirvaad Atta 5kg", 1, "5kg"), ("Toor Dal 1kg", 1, "1kg"), ("Tata Salt 1kg", 1, "1kg"), ("Fortune Mustard Oil 1L", 1, "1L")]
    },
    {
        "name": "Pooja & Sweet Prep",
        "time": "09:00 AM",
        "time_period": "Morning",
        "items": [("Besan (Gram Flour) 500g", 1, "500g"), ("Sugar (Loose)", 2, "1kg"), ("Amul Pure Ghee 1L", 1, "1L")]
    },
    {
        "name": "Kitchen Sanitation",
        "time": "06:15 PM",
        "time_period": "Evening",
        "items": [("Surf Excel Easy Wash 500g", 1, "500g"), ("Vim Dishwash Bar 155g", 2, "155g")]
    }
]

def seed_database():
    init_db()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check if historical transactions already exist in Supabase
            cur.execute("SELECT COUNT(*) FROM sale_items;")
            existing_count = cur.fetchone()["count"]

            if existing_count > 0:
                print(f"[Supabase] Historical transactions already seeded ({existing_count} rows). Skipping.")
                return

            print("[Supabase] Seeding 180 days with sale_no, time, weather, and festival data into PostgreSQL...")

            today = datetime.now()
            days_to_seed = 180
            item_lookup = {p["name"]: p for p in CATALOG_PRODUCTS}
            days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

            for day_offset in range(days_to_seed, -1, -1):
                sale_dt = today - timedelta(days=day_offset)
                sale_date_str = sale_dt.strftime("%Y-%m-%d")
                month_str = sale_dt.strftime("%Y-%m")
                day_of_week = days_names[sale_dt.weekday()]
                month_int = sale_dt.month

                if month_int in [5, 6]:
                    day_weather = random.choice(["Hot", "Hot", "Sunny"])
                    day_festival = "None"
                elif month_int in [7, 8]:
                    day_weather = random.choice(["Rainy", "Rainy", "Humid", "Overcast"])
                    day_festival = "None"
                elif month_int in [10, 11]:
                    day_weather = "Pleasant"
                    day_festival = random.choice(["Navratri Day 1", "Diwali Prep", "Dhanteras", "None", "None"])
                elif month_int in [12, 1]:
                    day_weather = "Cold"
                    day_festival = "Makar Sankranti" if month_int == 1 and sale_dt.day == 14 else "None"
                elif month_int == 3:
                    day_weather = "Sunny"
                    day_festival = "Holi" if sale_dt.day == 20 else "None"
                else:
                    day_weather = "Normal"
                    day_festival = "None"

                timeline_prog = 1.0 - (day_offset / days_to_seed)
                is_weekend = day_of_week in ["Saturday", "Sunday"]
                num_sales = random.randint(14, 20) if is_weekend else random.randint(10, 14)

                cur.execute("""
                    INSERT INTO sales_batches (batch_date, weather, festival, raw_json, items_count, total_revenue)
                    VALUES (%s, %s, %s, '{}'::jsonb, 0, 0.0)
                    RETURNING id;
                """, (sale_date_str, day_weather, day_festival))
                batch_id = cur.fetchone()["id"]

                batch_rev = 0.0
                batch_items = 0

                for s_no in range(1, num_sales + 1):
                    basket_id = f"BSK-{sale_date_str}-{s_no}"
                    pattern = random.choice(BASKET_PATTERNS)
                    sale_time = pattern["time"]
                    time_period = pattern["time_period"]

                    for item_name, base_qty, pack_size in pattern["items"]:
                        p_info = item_lookup[item_name]

                        w_mult = 1.0
                        if day_weather == "Rainy" and ("Tea" in item_name or "Maggi" in item_name):
                            w_mult = 1.7
                        elif day_weather == "Hot" and ("Cold Drink" in item_name or "Sting" in item_name or "Thums" in item_name or "Dahi" in item_name):
                            w_mult = 1.8
                        elif day_weather == "Cold" and ("Ghee" in item_name or "Tea" in item_name or "Oil" in item_name):
                            w_mult = 1.5

                        f_mult = 1.0
                        if "Navratri" in day_festival and ("Ghee" in item_name or "Dahi" in item_name):
                            f_mult = 1.9
                        elif "Diwali" in day_festival and ("Sugar" in item_name or "Besan" in item_name or "Ghee" in item_name):
                            f_mult = 2.4

                        trend_mult = 1.0 + (p_info["trend_bias"] - 1.0) * timeline_prog
                        chance = w_mult * f_mult * trend_mult
                        if chance < 0.6 and random.random() > chance:
                            continue

                        qty = float(base_qty)
                        unit_price = p_info["price"]
                        line_total = round(qty * unit_price, 2)

                        cur.execute("""
                            INSERT INTO sale_items (
                                batch_id, sale_no, sale_date, sale_time, time_period,
                                month_str, day_of_week, weather, festival,
                                basket_id, product_name, category, quantity, unit, pack_size,
                                unit_price, total_amount
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            batch_id, s_no, sale_date_str, sale_time, time_period,
                            month_str, day_of_week, day_weather, day_festival,
                            basket_id, item_name, p_info["category"], qty, p_info["unit"], pack_size,
                            unit_price, line_total
                        ))

                        batch_rev += line_total
                        batch_items += 1

                cur.execute("""
                    UPDATE sales_batches
                    SET items_count = %s, total_revenue = %s
                    WHERE id = %s;
                """, (batch_items, round(batch_rev, 2), batch_id))

            conn.commit()
            print("[Supabase] 180 days of transaction data seeded successfully into PostgreSQL!")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
