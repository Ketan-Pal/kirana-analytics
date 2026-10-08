# Kirana Demand & Pattern Forecasting System
### AI-Powered Basket Intelligence, Trend Sensing & Multi-Season Demand Forecasting

---

## 🎯 What This System Does

This platform is specifically designed to uncover **customer buying patterns**, detect **changing trends from past sales data**, and **forecast future demand** (Next Month, Upcoming Season, and Year-Round Festivals) for your Kirana store.

No unnecessary stock taking or credit ledger overhead—just pure **retail intelligence and demand prediction**.

---

## 📁 System Architecture

```
kirana-analytics/
├── migrations/           # Flyway-style SQL migrations (V1, V2, V3)
├── migration_runner.py   # Autonomous database migration runner
├── database.py           # Supabase PostgreSQL connection pooler (IPv4)
├── catalog_matcher.py    # Fuzzy alias & canonical product resolver
├── seed_data.py          # Synthetic multi-season Kirana transactions
├── ingestion.py          # Daily Gemini notepad JSON parser & batch pipeline
├── analytics.py          # Basket co-purchases, day-of-week & changing trends
├── forecasting.py        # Next-month SKU projections, seasonal & festival calendar
├── gemini_enricher.py    # Gemini AI FMCG retail intelligence enrichment layer
├── main.py               # FastAPI backend & interactive dark-mode dashboard
├── run.bat               # Windows launcher
└── README.md             # Guide & documentation
```

---

## 🚀 How to Run

1. **One-Click Launch:**
   Double-click [`run.bat`](file:///C:/Users/ketan/Documents/kirana-analytics/run.bat).
2. **Open in Browser:**
   - On this PC: `http://localhost:8000`
   - On your mobile (same Wi-Fi): `http://<your-pc-ip>:8000`

---

## 📊 Core Analytical Capabilities

### 1. 🛒 Customer Buying Patterns (Basket Dynamics)
- **Co-Purchasing Rules (FP-Growth Lift & Confidence):** Uncovers which items are consistently purchased together in the same bill (e.g., *Tea + Parle-G*, *Maggi + Thums Up*, *Milk + Marie Gold*).
- **Day-of-Week Shopping Behavior:** Analyzes how shopping shifts across Monday–Sunday (Weekday breakfast/daily staples vs. Weekend snacking and bulk replenishment).
- **Time-of-Day Shifts:** Morning breakfast runs vs. Evening munchies and dinner prep.

### 2. 📈 Changing Patterns & Trend Momentum (Past Data Analysis)
- **Surging Products (Fastest Demand Acceleration):** Highlights products with the highest growth rate over the recent 30-day window compared to the prior period.
- **Declining Products:** Flags items cooling down in sales volume or losing customer preference.
- **Historical 6-Month Volume Trend:** Visualizes monthly transaction volume and average spend per visit over time.

### 3. 🔮 Predictive Demand Forecasting
- **Next Month SKU Demand Projections:**
  - Calculates expected unit sales volume and revenue for every SKU for the upcoming month.
  - Combines recent run-rate velocity + trend momentum + seasonal weighting.
  - Generates clear **Stocking Directives** (e.g., *"Prepare inventory for ~180 packets (+25% vs last month)"*).
- **Upcoming Seasonal Shifts (Summer / Monsoon / Winter):**
  - Projects category-level demand swings as weather changes (e.g. cold drinks and dahi in summer; tea, fritters, and instant noodles in monsoon; ghee and hot beverages in winter).
- **🪔 12-Month Indian Festival Surge Calendar:**
  - Forward roadmap for Diwali, Navratri, Holi, Makar Sankranti, Eid, etc.
  - Shows days remaining, urgency status (Critical / Upcoming / Advance), and item-specific surge forecasts (+180% Sugar, +240% Besan, +210% Ghee) so you can order at wholesale before vendor prices rise.

### 4. ✨ Gemini AI Retail Strategy Advisor (Autonomous FMCG Consultancy)
- **Executive Strategic Brief:** Summarizes current store health and counter priorities in plain English with authentic Indian Kirana terminology.
- **Weather Tactical Directives:** Immediate counter and shelf positioning directives triggered by real-time rain/heat/cold correlations.
- **High-ROI Merchandising Combos:** Practical co-purchase bundles with specific margin-protective promotions (e.g. *"₹5 off on combo"*) and micro-shelf placement instructions designed for 150–300 sq.ft. Kirana formats.
- **Distributor Procurement & Timing Tips:** Proactive alerts on wholesale price surges, lead-time bottlenecks, and minimum order quantities before festival rushes.
- **Why-Behind-The-Trend Intelligence:** Qualitative retail context explaining *why* specific SKUs are surging or cooling in the neighbourhood.
- **Zero-Latency Cloud Caching:** Responses are cached in Supabase (`ai_insights_cache`) and automatically refreshed upon each daily notepad ingestion or manual button press.

---

## 🔄 Daily 2-Minute Workflow

1. **Snap Daily Notepad:** Take a photo of your handwritten sales notepad in the **Google Gemini Mobile App**.
2. **Run Prompt:** Paste the prompt from [`C:\Users\ketan\kirana_gemini_prompt.md`](file:///C:/Users/ketan/kirana_gemini_prompt.md) to receive clean JSON.
3. **Ingest to Dashboard:** Open `http://localhost:8000`, click **"Ingest Gemini Notepad JSON"**, and paste.
4. **Autonomous AI Synthesis:** The predictive models, basket patterns, growth trends, and **Gemini AI Retail Strategy Advisor** re-synthesize and update automatically!
