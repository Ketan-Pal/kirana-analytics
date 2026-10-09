# Kirana Demand Pattern & Predictive Forecasting System
### AI-Powered Basket Mining, Trend Momentum, Regional Festival Roadmaps & Autonomous Retail Advisory

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini%20Flash-8E75C2.svg)](https://ai.google.dev/)
[![OS Support](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-blueviolet.svg)](#-quickstart--installation-cross-platform)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 System Mission

The **Kirana Demand Pattern & Predictive Forecasting System** is a purpose-built retail intelligence platform designed specifically for Indian Kirana and neighbourhood grocery stores (150–300 sq. ft.).

Unlike conventional enterprise POS or ERP software that imposes tedious barcode scanning and credit ledger overhead, this system extracts **predictive retail intelligence** directly from traditional, handwritten daily counter sales notepads:
1. **Customer Buying Patterns:** Identifies high-lift co-purchase item combinations to design margin-boosting bundle deals.
2. **Changing Market Trends:** Analyzes 30-day velocity momentum to alert the storekeeper to surging vs. cooling grocery products.
3. **Multi-Horizon Demand Forecasting:** Projects next-month SKU volumes, weather-driven swings (Summer cooling vs. Monsoon snacking vs. Winter staples), and a 12-month advance Indian festival roadmap.
4. **$0 Dynamic Market Trend Sensing:** Autonomously crawls the web keylessly via DuckDuckGo and synthesizes modern festive demand shifts using Gemini Flash without costly search grounding APIs.
5. **Autonomous AI Strategy Advisor:** Acts as a 24/7 seasoned FMCG retail consultant, delivering actionable shelf placement directives, promo deals, and distributor timing advice.

---

## 📁 Repository Structure

```
kirana-analytics/
├── migrations/               # Flyway-style SQL schema migrations
│   ├── V1__initial_schema.sql        # Sales batches, items, and schema versioning
│   ├── V2__seed_catalog_products.sql # 27 canonical FMCG products & aliases
│   ├── V3__ai_insights_cache.sql     # AI insights caching table
│   └── V4__festival_calendar.sql     # Regional festival calendar & surge items
├── analytics.py              # Basket pairs, weekday/weekend, and trend momentum
├── catalog_matcher.py        # Fuzzy alias matcher & auto-registration
├── database.py               # Supabase PostgreSQL connection pooler (IPv4/SSL)
├── festival_service.py       # Regional holiday sync with Render cold-start buffer
├── festival_trend_crawler.py # 4-phase keyless DuckDuckGo + Gemini trend crawler
├── forecasting.py            # Run-rate extrapolation forecaster & seasonal roadmap
├── gemini_enricher.py        # Gemini retail strategy advisor & model cascading
├── gemini_prompt.md          # Daily mobile OCR prompt (copy-paste for Gemini mobile app)
├── ingestion.py              # Notepad JSON ingestion pipeline
├── main.py                   # FastAPI web server & dashboard UI
├── migration_runner.py       # Autonomous migration execution & verification tool
├── seed_data.py              # Synthetic 180-day transactional dataset generator
├── run.bat                   # Windows 1-click startup batch script
├── requirements.txt          # Python dependencies for Linux & Windows
├── GEMINI.md                 # Project rules & preferences
├── .env.example              # Environment variables template
└── README.md                 # Complete project knowledge base (this document)
```

---

## 🚀 Quickstart & Installation (Cross-Platform)

### Prerequisites
- Python 3.10 or higher
- Supabase PostgreSQL database (Free Tier)
- Google Gemini API key (Free Tier from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/Ketan-Pal/kirana-analytics.git
cd kirana-analytics
```

### 2. Set Up Virtual Environment & Dependencies

#### On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### On Windows:
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template and configure your credentials:

#### Linux / macOS:
```bash
cp .env.example .env
```

#### Windows:
```cmd
copy .env.example .env
```

Edit `.env` with your preferred editor:
```ini
DATABASE_URL=postgresql://postgres.xxx:[YOUR_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
GEMINI_API_KEY=AIzaSy...
ALLOW_SYNTHETIC_SEED=false
```

### 4. Run Database Migrations
Initialize database tables, canonical products, and version tracking:
```bash
python migration_runner.py migrate
```

### 5. Launch the Server

#### Linux / macOS:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Windows:
Double-click `run.bat` or run:
```cmd
python main.py
```

Open your browser at **`http://localhost:8000`** (or access from your mobile phone on the same Wi-Fi network at `http://<your-local-ip>:8000`).

---

## 🔄 Daily 2-Minute Merchant Workflow

```
[Store Closing: 9:30 PM] 
   └── 📸 Take photo of handwritten paper notepad with smartphone
   └── 💬 Send photo to Gemini Mobile App with prompt from ./gemini_prompt.md
   └── 📋 Copy transcribed JSON output
   └── 🌐 Open dashboard -> Click "📥 Ingest Notepad JSON" -> Paste & Submit
   └── ⚡ Analytics, forecasts, and AI strategy advisor update instantly!
```

---

## 📖 Deep-Dive Knowledge Base & Technical Guides

<details>
<summary><b>🏛️ Architecture & System Blueprint</b></summary>

### End-to-End System Data Flow
```mermaid
flowchart TD
    subgraph Capture["1. Daily Paper Capture"]
        A["Handwritten Sales Notepad"] --> B["Google Gemini Mobile OCR"]
        B --> C["Clean Structured Sales JSON"]
        C --> D["POST /api/ingest"]
    end

    subgraph DataStore["2. Persistent Database (Supabase PostgreSQL)"]
        D --> E[("sales_batches & sale_items")]
        E --> F[("catalog_items (Canonical Dictionary)")]
        E --> G[("festival_calendar (Regional Gazette + Web Trends)")]
        E --> H[("ai_insights_cache (Strategy Cache)")]
    end

    subgraph AnalyticsEngine["3. Analytics & Predictive Engines"]
        E --> I1["Basket Co-Purchases (FP-Growth Lift)"]
        E --> I2["Day-of-Week & Time-of-Day Dynamics"]
        E --> I3["Weather Correlation Engine"]
        E --> I4["30-Day Trend Momentum (Surging vs Declining)"]
        E --> I5["Next-Month SKU Demand Forecaster (Run-Rate Extrapolation)"]
    end

    subgraph ExternalServices["4. Zero-Cost External Sensing"]
        J1["Indian Gov Regional Calendar API"] -->|Strict 30D Rate-Limit| G
        J2["DuckDuckGo HTML Search (Keyless)"] -->|Free Web Snippets| J3["Gemini Flash Synthesis"]
        J3 -->|Modern Festive Shifts| G
    end

    subgraph Advisor["5. AI Retail Advisor"]
        AnalyticsEngine --> K["Gemini Flash FMCG Advisory"]
        G --> K
        K --> H
    end

    subgraph Presentation["6. Countertop Storefront Dashboard"]
        AnalyticsEngine --> L["Interactive Dark-Mode Dashboard (:8000)"]
        H --> L
        G --> L
    end
```

### Core Components
- **FastAPI Core (`main.py`):** High-performance async ASGI application serving REST endpoints and dark-mode storefront UI.
- **Connection Pooler (`database.py`):** Supabase PostgreSQL pooled connections using `psycopg2` dictionary cursor factory with SSL mode require.
- **Migration Runner (`migration_runner.py`):** Autonomous Flyway-compatible version control enforcing migration order and SHA-256 script checksums.
- **Catalog Matcher (`catalog_matcher.py`):** Fuzzy string distance matcher (`difflib.SequenceMatcher`) that links colloquial Hindi/Hinglish terms to standardized catalog items and auto-registers new products.

</details>

---

<details>
<summary><b>📝 Daily Paper Notepad Format & OCR Transcription Guide</b></summary>

### The Approved Notepad Table Format
Shopkeepers record daily counter transactions in this structured tabular format:

```text
Date: 07/10/2026

sale no. | time     | products quantity and size     | total amount | weather | festival
-----------------------------------------------------------------------------------------
1        | 08:15 AM | 2 amul taaza 500, 1 marie 120g | 69           | Rainy   | None
2        | 10:30 AM | 1 tea 250g, 2kg cheeni, 2 parle| 245          | Rainy   | None
3        | 01:20 PM | 1 aashirvaad 5k, 1 toor dal 1k | 400          | Rainy   | None
4        | 05:45 PM | 3 maggi 70g, 2 sting 250ml     | 82           | Rainy   | None
5        | 07:30 PM | 1 ghee 1L, 2kg cheeni, 1 besan | 755          | Pleasant| Navratri Day 1
```

### How Each Column Powers the Analytics Engines
| Column | What You Write | How Our System Uses It |
| :--- | :--- | :--- |
| **Date** *(Top)* | `07/10/2026` or `07 Oct` | **Time-Series Tracking:** Anchors historical trends, monthly rollups, and demand forecasting. |
| **`sale no.`** | `1`, `2`, `3`... | **Customer Basket Grouping:** Identifies all items in the same bill to calculate FP-Growth co-purchase lift and basket size. |
| **`time`** | `08:15 AM`, `06:30 PM` | **Hourly Rush Analysis:** Categorizes sales into Morning (breakfast/milk), Afternoon (refreshments), and Evening (snacks/dinner prep). |
| **`products quantity and size`** | `2 amul taaza 500`<br>`3 maggi 70g`<br>`cheeni 2kg` | **SKU Velocity & Pack Preference:** Distinguishes quantity sold from pack size; fuzzy matcher maps informal names to standard inventory. |
| **`total amount`** | `69`, `82`, `755` | **Basket Spend & Revenue:** Computes average spend per visit and overall daily revenue. |
| **`weather`** | `Sunny`, `Rainy`, `Hot`, `Cold` | **Weather Demand Sensing:** Correlates weather conditions with sales surges (e.g. tea & noodles on rainy days; cold drinks in heat). |
| **`festival`** | `None`, `Navratri Day 1`, `Diwali Prep` | **Cultural Surge Forecaster:** Captures festive ingredient surges (Ghee, Sugar, Besan, Fasting items). |

### Practical Counter Writing Tips
1. **Weather & Festival Shortcut:** If conditions remain constant all day, write them once at the top of the notepad page (e.g. `Date: 07/10 | Weather: Rainy | Festival: None`). You don't need to rewrite them on every row.
2. **Products Shorthand:** Abbreviations are fully supported (`taaza 500`, `namak 1k`, `maggi 3`, `tel 1L`).
3. **Price Omission:** In rush hours, writing individual line prices is optional—writing the line's `total amount` is sufficient.

---

### Google Gemini Vision OCR Prompt
Copy and paste this prompt along with your notepad photo into the Google Gemini Mobile App:

```text
You are an expert Indian Kirana retail data specialist. I have attached a photo of my daily sales handwritten notepad page.

The notepad is written in this tabular format:
- Top: Date (e.g., 07/10/2026 or 07 Oct)
- Columns: [sale no.]  [time]  [products quantity and size]  [total amount]  [weather]  [festival]

Your task is to transcribe, interpret, clean, and convert each sale entry into a structured JSON record.

### Parsing Guidelines:
1. "sale no." -> Customer bill/sale number (1, 2, 3...) used for customer basket grouping.
2. "time" -> Transcribe time (e.g., "8:30 AM", "6:15 PM"). Auto-classify into time_period: "Morning" (6AM-12PM), "Afternoon" (12PM-5PM), "Evening" (5PM-9PM), or "Night" (9PM onwards).
3. "products quantity and size" -> Split individual items in the customer's purchase:
   - Handle informal names ("amul taaza 500", "tata namak 1k", "cheeni 2kg", "3 maggi", "surf 500g", "2 sting").
   - Extract standardized name, quantity (count or weight), unit (packet, kg, bottle, piece), and pack size (e.g. 500ml, 1kg, 250ml).
4. "total amount" -> Extract the bill total amount (₹).
5. "weather" -> Transcribe the weather condition (e.g., Sunny, Rainy, Hot, Cold, Normal). If written once at the top, apply to all entries.
6. "festival" -> Transcribe the festival or occasion (e.g., None, Navratri, Diwali, Holi, Sunday Rush).

### Strict Output Format:
Return ONLY the following JSON structure:
{
  "date": "YYYY-MM-DD",
  "day_weather": "Sunny | Rainy | Hot | Cold | Normal",
  "day_festival": "None | Navratri | Diwali | Holi | etc.",
  "sales": [
    {
      "sale_no": 1,
      "time": "08:30 AM",
      "time_period": "Morning | Afternoon | Evening | Night",
      "bill_total": 69.0,
      "weather": "Rainy",
      "festival": "None",
      "items": [
        {
          "raw_text": "2 amul taaza 500",
          "standardized_name": "Amul Taaza Milk 500ml",
          "category": "Dairy | Staples | Snacks | Beverages | Personal Care | Cleaning | Other",
          "quantity": 2,
          "unit": "packet",
          "pack_size": "500ml",
          "unit_price": 27.0,
          "line_total": 54.0
        }
      ]
    }
  ]
}
```

</details>

---

<details>
<summary><b>📊 Customer Basket Mining & Trend Momentum Analytics</b></summary>

### 1. Market Basket Analysis (FP-Growth Lift & Confidence)
Identifies items that frequently appear together in the same customer basket:
- **Support:** $P(A \cap B) = \frac{\text{Transactions with both } A \text{ and } B}{\text{Total Baskets}}$
- **Confidence:** $P(B \mid A) = \frac{\text{Transactions with both } A \text{ and } B}{\text{Transactions with } A}$
- **Lift:** $\text{Lift}(A \to B) = \frac{P(A \cap B)}{P(A) \times P(B)}$
  - $\text{Lift} > 1.0$: Strong positive association (buying $A$ significantly drives purchase of $B$).
  - Used by the AI advisor to recommend bundles like *Milk + Biscuits* or *Tea + Sugar*.

### 2. Statistical Sample Gating Guard
During the first week of store operation, computing co-purchase lift on just 3–5 bills can produce statistically distorted 100% confidence scores.
- **Threshold:** The engine enforces a minimum threshold of **25 recorded bills**.
- **Cold-Start Response:** When bills $< 25$, the system returns:
  ```json
  {
    "status": "sample_gating",
    "is_gated": true,
    "recorded_bills": 12,
    "threshold_bills": 25,
    "message": "Accumulating basket combinations (12/25 bills recorded)"
  }
  ```
  The dashboard displays an informative progress indicator rather than skewed recommendations.

### 3. 30-Day Velocity Momentum & Zero-Division Guard
The trend engine measures demand acceleration by comparing the recent 30-day window against the prior 30-day window:
$$\text{Growth \%} = \left(\frac{\text{Recent 30D Qty} - \text{Prior 30D Qty}}{\text{Prior 30D Qty}}\right) \times 100$$
- **Surging Items:** Growth $\ge +15.0\%$
- **Declining Items:** Growth $\le -10.0\%$
- **Zero-Division Handling:** When $\text{Prior 30D Qty} = 0$ (e.g. newly introduced products or store Days 1–30), growth is returned as `0.0%` with status `"Baseline Accumulating"`, eliminating division-by-zero crashes.

</details>

---

<details>
<summary><b>🔮 Triple-Layer Predictive Demand Forecasting Engine</b></summary>

### Forecasting Architecture
The forecaster generates unit volume and revenue projections for the upcoming month using three compounding analytical layers:

```mermaid
flowchart LR
    A["Layer 1: Base Velocity<br/>(Last 30-Day Volume)"] --> D["Next Month Forecast"]
    B["Layer 2: Trend Momentum<br/>(Recent 30D vs Prior 30D)"] --> D
    C["Layer 3: Seasonal Lift Index<br/>(Target Month Weather / Events)"] --> D
```

### Mathematical Formulas

#### 1. Base Run-Rate & Early Extrapolation (Days 1–29)
When a store opens, waiting a full 30 days before generating forecasts is unacceptable. The engine applies dynamic daily run-rate extrapolation:
$$\text{Run-Rate Extrapolated Qty} = \text{Current Recorded Qty} \times \left(\frac{30}{\text{Active Recorded Days}}\right) \quad (\text{for } 1 \le \text{Active Days} < 30)$$
When $\text{Active Days} \ge 30$, the multiplier is $1.0$. If $\text{Active Days} = 0$, a clean cold-start empty state is returned.

#### 2. Growth Momentum Damping
To avoid extreme purchasing fluctuations caused by short-term spikes, momentum is damped between $-25\%$ and $+35\%$:
$$\text{Growth Rate} = \frac{\text{Current Qty} - \text{Prior Qty}}{\max(1, \text{Prior Qty})}$$
$$\text{Damped Growth} = \max(-0.25, \min(0.35, \text{Growth Rate}))$$

#### 3. Seasonal Lift Multipliers
Each target calendar month maps to its respective Indian climate season:
- **Summer (March–June):** Beverages & Dahi $\times 1.25$
- **Monsoon (July–September):** Tea & Instant Noodles $\times 1.20$, Besan (Frying) $\times 1.15$
- **Festive (October–November):** Ghee, Sugar & Besan $\times 1.30$, Basmati Rice $\times 1.20$
- **Winter (December–February):** Pure Ghee $\times 1.25$, Tea $\times 1.20$, Mustard Oil $\times 1.15$

#### 4. Final SKU Projection
$$\text{Projected Next Month Qty} = \text{round}\Big(\text{Run-Rate Qty} \times (1 + \text{Damped Growth}) \times \text{Seasonal Lift}\Big)$$
$$\text{Projected Revenue} = \text{Projected Qty} \times \text{Unit Price}$$

</details>

---

<details>
<summary><b>🪔 Regional Festival Calendar Sync (ADR-001)</b></summary>

### Official Regional Gazette Sync
Festivals in India shift annually based on lunisolar calculations. Hardcoded dates lead to inaccurate inventory planning.
- **API Source:** `https://calendar-api-d7a8.onrender.com/v1/holidays?country=IN&region=UP&year={year}` (data source: Official Gazette of India / `india.gov.in`).
- **Target Coverage:** Major regional celebrations including Diwali, Dhanteras, Navratri, Holi, Makar Sankranti, Raksha Bandhan, Janmashtami, and Eid.

### Strict Rate-Limit Enforcement
The public calendar API endpoint enforces strict rate limits.
- **Database Caching:** All dates, preparation lead times, surge categories, and items are stored in Supabase table `festival_calendar`.
- **Monthly Sync Rule:** On request, the system checks `MAX(updated_at)` for the year. If updated within the last 30 days, the external API call is skipped:
  ```json
  {
    "status": "skipped",
    "reason": "Festival calendar for 2026 is fresh (synced 0 days ago). Rate limits preserved."
  }
  ```
- **Zero Runtime Overhead:** Store operations and dashboard rendering query Supabase locally (0 external API calls during daily store use).

### Render Free-Tier Cold-Start Tolerance
The calendar API is hosted on Render's free tier, which sleeps after 15 minutes of inactivity and takes 15–25 seconds to spin up.
- **Client Timeout:** Configured with a 25.0-second safety timeout in `festival_service.py`.
- **Deterministic Baseline Fallback:** If Render is sleeping or the network is unreachable, the service catches the read timeout gracefully, populates Supabase from verified deterministic gazette dates, and serves `/api/festival-roadmap` with `200 OK` and 0 downtime.

</details>

---

<details>
<summary><b>🌐 $0 Keyless Dynamic Festival Trend Crawler</b></summary>

### The Challenge with Hardcoded Trends
Consumer tastes change over time:
- In Holi, packaged chocolate gift hampers increasingly replace loose mithai boxes.
- Health awareness drives surges in organic herbal gulaal and ready-to-mix thandai.
- Hardcoding static product lists causes shopkeepers to miss high-margin modern retail shifts.

### Zero-Cost Agentic Architecture
Paid Google Search Grounding costs **$35 per 1,000 requests**. We eliminated this cost entirely with a keyless 4-phase loop:

```mermaid
sequenceDiagram
    autonumber
    actor Merchant as Storekeeper / App
    participant Backend as FastAPI Backend
    participant Gemini as Gemini Flash API
    participant DDG as DuckDuckGo (HTML / Keyless)
    participant DB as Supabase PostgreSQL

    Merchant->>Backend: POST /api/festival-trend/crawl?festival=Holi
    Backend->>Gemini: Formulate 3 FMCG Retail Search Queries
    Gemini-->>Backend: Return JSON Queries
    loop For Each Query
        Backend->>DDG: Fetch Search Result Snippets (0 Tokens, 0 Cost)
        DDG-->>Backend: Return Clean HTML Snippets
    end
    Backend->>Gemini: Synthesize Search Snippets into FMCG Surges & Reasons
    Gemini-->>Backend: Return Validated Retail JSON (Items, % Surge, Advice)
    Backend->>DB: UPDATE festival_calendar (surge_categories, surge_items, source)
    Backend-->>Merchant: 200 OK (Card Updates to Live Web Trends)
```

### In-Dashboard Trigger Button
Each festival card in the **12-Month Indian Festival Surge Roadmap** includes a **"⚡ Sense Live Trends"** button. Clicking it triggers the crawler, updates the database, and switches the card badge from `🏛️ Regional Gazette` to `🌐 Live Web Trends`.

</details>

---

<details>
<summary><b>✨ Autonomous AI Retail Strategy Advisor</b></summary>

### Model Cascading & Fault Tolerance
The advisor synthesizes multi-dimensional mathematical outputs (baskets, momentum, weather, forecasts, festivals) into plain-English retail directives.

To guarantee zero downtime during peak Google API traffic, `gemini_enricher.py` implements multi-tier fallback:
1. **Primary Model:** `gemini-3.8-flash` (rich reasoning).
2. **First Fallback:** `gemini-flash-lite-latest` (fast 5-second recovery from 503 Service Unavailable errors).
3. **Second Fallback:** `gemini-flash-latest`.
4. **Offline Fallback:** Deterministic FMCG rule-based advisor (active when no internet or API key is available).

### Output Structure
- **Daily Executive Brief:** 2–3 sentences highlighting counter priorities for today.
- **Weather Tactical Action:** Immediate positioning alerts (e.g. *"Place tea bags and 2-minute noodles on front glass counters ahead of evening rain"*).
- **Merchandising Combos:** Practical bundles with specific rupee discounts (e.g. *"Save ₹5 on Chai + Biscuit Combo"*) and micro-space shelf placement directives designed for small shops.
- **Distributor Timing Tips:** Warnings on wholesale price increases and distributor lead times before festival rushes.

All insights are cached in Supabase table `ai_insights_cache` to ensure instantaneous dashboard loading.

</details>

---

<details>
<summary><b>🚀 Day 0 Production Readiness Checklist & Merchant Runbook</b></summary>

### Cold-Start 4-Stage Progressive Unlocking Schedule
When launching with zero historical transactions, capabilities unlock progressively as receipts are logged:

| Timeline | Milestone | Intelligence Unlocked | Merchant Experience |
| :--- | :--- | :--- | :--- |
| **Day 0** | Clean Slate (0 Bills) | Cold-start state active | UI displays *"Stage 1: Volume Accumulating"*; informative empty states guide next steps. |
| **Days 1–7** | Volume Baselines | Day & time dynamics | Daily revenue tracking; weekday vs. weekend velocity patterns begin emerging. |
| **Days 8–14** | Basket Mining | 25+ Bills recorded | Co-purchase combinations unlock; AI Advisor generates high-lift combo promotions. |
| **Days 15–29**| Demand Forecast | Run-rate extrapolation | Forecaster calculates 30-day run-rate SKU orders ahead of distributor visits. |
| **Day 30+** | Trend Momentum | Full predictive engine | 30-day momentum engine flags surging (+15%) vs declining (-10%) grocery products. |

### Pre-Flight Launch Verification
1. **Migrations Verified:** Run `python migration_runner.py info` to confirm that all 4 Flyway migrations (`V1` to `V4`) are applied.
2. **Environment Secured:** Confirm `ALLOW_SYNTHETIC_SEED=false` in `.env` to prevent test dummy data from polluting production accounting.
3. **API Health Check:** Confirm that `/api/festival-roadmap` returns `200 OK`.

</details>

---

## 🔒 Security, Privacy & Zero-Cost Policy

- **Zero Hardcoded Credentials:** All database connection strings and API keys are loaded via environment variables (`.env`), which is strictly excluded from Git tracking.
- **SQL Injection Immune:** All database interactions in `analytics.py`, `forecasting.py`, `ingestion.py`, and `database.py` use parameterized queries (`%s`).
- **100% Free Tier Architecture:**
  - Supabase PostgreSQL: Free Tier (500MB storage supports >100,000 line items).
  - Google Gemini: Free Tier (15 RPM free, insights cached in DB).
  - Indian Calendar API: Free Tier (cached for 30 days).
  - DuckDuckGo: Free HTML search (keyless, zero tokens).

---

## 📄 License

Built for Indian Kirana Store Empowerment. Open source under the [MIT License](https://opensource.org/licenses/MIT).
