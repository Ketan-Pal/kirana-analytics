# Production Readiness Task List & Architectural Decisions
### Kirana Demand Pattern & Predictive Forecasting System

---

## 📌 Architectural Decision Record (ADR)

### ADR-001: Regional Government Calendar API Sync (Zero-Maintenance Festival Calendar)
- **Context:** Indian festivals follow astronomical lunar calendars (Hindu Panchang / Islamic Hijri) where Gregorian dates change each year. Hardcoding dates requires annual code modifications by a developer.
- **Decision:** Integrate the **Official Indian Regional Calendar API** (`https://calendar-api-d7a8.onrender.com/v1/holidays?country=IN&region=UP&year={YEAR}`, sourced from `india.gov.in/calendar`) instead of annual Gemini AI prompting.
- **Why this is superior to LLM-prompted calendar sync:**
  1. **Deterministic & Authoritative:** Sourced directly from official Government of India Gazetted Schedules (`india.gov.in`), eliminating LLM hallucinations or variations in lunar interpretations.
  2. **Regional Granularity:** Supports state-specific regional gazettes (`region=UP`), capturing Uttar Pradesh and local cultural observances.
  3. **Zero Developer Work:** Dynamically parameterized by year (`year={current_year}`). When 2027 arrives, the system queries 2027 automatically without code changes.
  4. **Zero API Cost & High Performance:** Fast HTTP REST endpoint; does not consume Gemini LLM token quotas.
- **Rate Limit & Sync Frequency Policy:**
  - **Strict Rate Limits:** The Render-hosted Calendar API enforces strict rate limits. It MUST NEVER be called on dashboard page loads or during real-time requests.
  - **Cadence (Once a Month / Once a Year):** The API is invoked at most **once a month** (or annually on January 1st) via a background cron or persistent sync script.
  - **Persistent Supabase Storage:** Fetched holiday data is persisted into Supabase (`festival_calendar` table). All runtime forecast lookups query the database directly with zero external API latency or rate-limit consumption.
  - **Surge Multiplier Mapping:** Maps official holidays (Diwali, Dussehra/Navratri, Holi, Makar Sankranti, Eid, Raksha Bandhan) to Kirana FMCG demand surge factors (Sugar $+180\%$, Besan $+240\%$, Ghee $+210\%$).
- **Local Ground-Truth:** Daily notepad annotations in the `festival` column (`festival: Navratri Day 1`) serve as local store validation for multi-day fasting and preparation lead times.
- **Maintenance Cost:** **Zero developer intervention** post-production launch.

---

## ✅ Completed Milestones

### 🌟 Milestone v0.0.4: Gemini AI Analytics Enrichment Layer
- [x] **V3 Migration (`migrations/V3__ai_insights_cache.sql`):** Applied on Supabase PostgreSQL for zero-latency insights caching.
- [x] **Enrichment Engine (`gemini_enricher.py`):** Multi-model synthesis (`gemini-3.8-flash` primary with automatic fallback to `gemini-flash-lite-latest` and deterministic baseline).
- [x] **Pipeline Ingestion Trigger (`ingestion.py`):** Automatically triggers fresh AI strategy synthesis upon daily notepad upload.
- [x] **FastAPI Endpoints (`main.py`):** Connected `GET /api/ai-insights` and `POST /api/ai-insights/refresh`.
- [x] **Dashboard UI Integration (`main.py`):** Added **"✨ Gemini AI Retail Strategy Advisor"** card featuring:
  - Daily Executive Strategy Brief
  - Weather Tactical Action Directive with priority counter SKUs
  - Enriched Merchandising Combos (item pair, consumer psychology, combo discount deal, and shelf placement directive)
  - Distributor Procurement & Timing Tips (wholesale price locking & lead-time alerts)
  - "Why-Behind-The-Trend" FMCG Context
  - Interactive "⚡ Re-Synthesize Strategy" button with real-time loading feedback.

---

## 🛠️ Production Hardening Tasks (Cold-Start & Zero-Dummy-Data)

- [x] **TASK-001: Mathematical Divide-by-Zero & Infinite Momentum Guards**
  - Updated `analytics.py`: when `prior_qty == 0` (Days 1–30 baseline accumulation), momentum returns `0.0` and flags as `"Baseline Accumulating"` instead of displaying $+100\%$.
  - Wrapped SQL aggregations with `COALESCE(SUM(...), 0)`.

- [x] **TASK-002: Startup Hook Decoupling (Pure DDL vs. Synthetic Data)**
  - Decoupled `main.py` startup: `on_startup()` executes Flyway migrations (`init_db()`) and strictly isolates `seed_database()` behind `ALLOW_SYNTHETIC_SEED=true`.
  - Added `ALLOW_SYNTHETIC_SEED=false` to `.env` and `.env.example`. In production, transaction tables start 100% empty on Day 1.

- [x] **TASK-003: Basket Co-Purchase Sample Gating (Apriori / Lift Thresholds)**
  - Added statistical sample gating to `get_basket_co_purchases()` in `analytics.py`: requires minimum 25 recorded bills before computing lift rules.
  - Returns informative status: `"Accumulating basket combinations (X/25 bills recorded)"` and updated frontend UI to display gating badge.

- [x] **TASK-004: Early Demand Forecast Extrapolation (Days 1–29 Fallback)**
  - Updated `forecasting.py`: during initial store operation (`1 <= active_days < 30`), extrapolates daily run-rate: `(current_qty * (30 / active_days))` to prevent underpredicting volume.
  - Implemented clean cold-start empty state when `active_days == 0`.

- [x] **TASK-005: Preserve Canonical FMCG Catalog (V2 Migration Ground Truth)**
  - Retained `V2__seed_catalog_products.sql` as the canonical master catalog for Indian FMCG staples.
  - Verified `catalog_matcher.py` dynamic auto-registration of unseen items while preserving canonical entries.

- [x] **TASK-006: UI Empty States & Progressive Intelligence Unlocking**
  - Integrated 4-Stage Progressive Unlocking indicator banner into `main.py` dashboard:
    - Stage 1 (Days 1–3): Baseline daily volume.
    - Stage 2 (Days 4–14): Day-of-week shopping shifts & early basket pairings.
    - Stage 3 (Days 15–30): Extrapolated next-month forecast & weather sensitivities.
    - Stage 4 (Day 31+): Full month-over-month momentum & surge acceleration.
  - Replaced raw table blanks with cold-start onboarding states.

---

## 🌟 Milestone v0.0.5: Dynamic Festival Intelligence & Production Hardening
- [x] **V4 Migration (`migrations/V4__festival_calendar.sql`):** Applied on Supabase PostgreSQL for persistent festival calendar storage.
- [x] **Regional Calendar Service (`festival_service.py`):** Implemented ADR-001 with strict rate-limited caching (max once a month/year sync against `india.gov.in` calendar API).
- [x] **Keyless Trend Crawler (`festival_trend_crawler.py`):** Agentic loop formulating search queries via Gemini, executing free DuckDuckGo searches, and synthesizing structured FMCG trend definitions ($0 cost).
- [x] **Roadmap Integration (`forecasting.py` & `main.py`):** Connected `/api/festival-roadmap` to query Supabase `festival_calendar` table and exposed `/api/festival-trend/crawl`.
