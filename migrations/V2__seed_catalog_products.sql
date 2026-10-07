-- V2__seed_catalog_products.sql
-- Flyway DML Migration: Master Product Catalog Seeding

INSERT INTO catalog_items (name, category, standard_unit, default_price, seasonality_tag, aliases)
VALUES
    ('Aashirvaad Atta 5kg', 'Staples', 'packet', 240.00, 'All-Season', '["aashirvaad 5k", "atta 5kg", "gehu aata"]'::jsonb),
    ('Tata Salt 1kg', 'Staples', 'packet', 28.00, 'All-Season', '["tata namak", "namak 1k", "tata salt"]'::jsonb),
    ('Sugar (Loose)', 'Staples', 'kg', 45.00, 'Festive', '["cheeni", "sugar", "sakkar"]'::jsonb),
    ('Toor Dal 1kg', 'Staples', 'kg', 160.00, 'All-Season', '["toor dal", "arhar dal", "tuvar dal"]'::jsonb),
    ('Fortune Mustard Oil 1L', 'Staples', 'bottle', 155.00, 'Winter', '["fortune tel", "mustard oil", "sarson tel"]'::jsonb),
    ('India Gate Basmati Rice 1kg', 'Staples', 'packet', 130.00, 'Festive', '["basmati rice", "chawal"]'::jsonb),
    ('Besan (Gram Flour) 500g', 'Staples', 'packet', 55.00, 'Festive', '["besan", "chana besan"]'::jsonb),
    ('Amul Pure Ghee 1L', 'Staples', 'tin', 610.00, 'Winter', '["amul ghee", "ghee 1l", "desi ghee"]'::jsonb),

    ('Amul Taaza Milk 500ml', 'Dairy', 'packet', 27.00, 'All-Season', '["amul taaza", "taaza 500", "amul doodh"]'::jsonb),
    ('Amul Gold Milk 500ml', 'Dairy', 'packet', 33.00, 'All-Season', '["amul gold", "gold 500"]'::jsonb),
    ('Amul Masti Dahi 400g', 'Dairy', 'cup', 36.00, 'Summer', '["amul dahi", "dahi", "masti dahi"]'::jsonb),
    ('Amul Butter 100g', 'Dairy', 'piece', 58.00, 'All-Season', '["amul butter", "butter 100g"]'::jsonb),

    ('Maggi 2-Minute Noodles 70g', 'Snacks', 'packet', 14.00, 'Monsoon', '["maggi", "maggie", "maggi packet"]'::jsonb),
    ('Parle-G Biscuits 100g', 'Snacks', 'packet', 10.00, 'All-Season', '["parle g", "parle-g", "glucose biscuit"]'::jsonb),
    ('Britannia Marie Gold 120g', 'Snacks', 'packet', 15.00, 'All-Season', '["marie gold", "marie biscuit"]'::jsonb),
    ('Britannia Good Day 100g', 'Snacks', 'packet', 20.00, 'All-Season', '["good day", "goodday"]'::jsonb),
    ('Lay''s Magic Masala 50g', 'Snacks', 'packet', 20.00, 'All-Season', '["lays blue", "lays masala"]'::jsonb),
    ('Haldiram Aloo Bhujia 200g', 'Snacks', 'packet', 55.00, 'Festive', '["aloo bhujia", "haldiram bhujia"]'::jsonb),

    ('Brooke Bond Red Label Tea 250g', 'Beverages', 'packet', 135.00, 'Winter', '["red label chai", "chai patti", "tea"]'::jsonb),
    ('Thums Up 250ml Bottle', 'Beverages', 'bottle', 20.00, 'Summer', '["thums up", "thumsup", "cold drink"]'::jsonb),
    ('Sting Energy Drink 250ml', 'Beverages', 'bottle', 20.00, 'Summer', '["sting", "energy drink"]'::jsonb),
    ('Frooti Mango Drink 160ml', 'Beverages', 'tetra', 10.00, 'Summer', '["frooti", "mango drink"]'::jsonb),

    ('Surf Excel Easy Wash 500g', 'Cleaning', 'packet', 75.00, 'All-Season', '["surf excel", "surf 500g", "washing powder"]'::jsonb),
    ('Vim Dishwash Bar 155g', 'Cleaning', 'piece', 20.00, 'All-Season', '["vim bar", "vim sabun"]'::jsonb),
    ('Dettol Soap 75g', 'Personal Care', 'piece', 40.00, 'Monsoon', '["dettol soap", "dettol sabun"]'::jsonb)
ON CONFLICT (name) DO NOTHING;
