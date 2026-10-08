# Production Readiness Task List & Architectural Decisions
### Kirana Demand Pattern & Predictive Forecasting System

---

## 📌 Architectural Decision Record (ADR)

### ADR-001: Autonomous Annual AI Sync (Zero-Maintenance Festival Calendar)
- **Context:** Indian festivals follow astronomical lunar calendars (Hindu Panchang / Islamic Hijri) where Gregorian dates change each year. Hardcoding dates requires annual code modifications by a developer.
- **Decision:** Implement an **Autonomous Annual AI Sync** routine. On January 1st of each year (or whenever a new calendar year begins), the background engine automatically queries Google Gemini for the verified dates of all major Indian festivals (Diwali, Navratri, Holi, Eid, Makar Sankranti, etc.) for that year, and updates the Supabase `festival_calendar` table autonomously.
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

- [ ] **TASK-001: Mathematical Divide-by-Zero & Infinite Momentum Guards**
  - Update `analytics.py` momentum calculation: when `prior_qty == 0` (Days 1–30), return `0.0` and flag as `"Baseline Accumulating"` instead of throwing zero-division errors or displaying $+100,000\%$ growth.
  - Wrap all SQL aggregation queries with `COALESCE` and null-safe checks.

- [ ] **TASK-002: Startup Hook Decoupling (Pure DDL vs. Synthetic Data)**
  - Decouple `main.py` startup: ensure `on_startup()` executes strictly Flyway migrations (`init_db()`).
  - Completely isolate `seed_data.py` (synthetic test data generator) behind an environment flag `ALLOW_SYNTHETIC_SEED=false`.
  - In production, `sale_items` and `sales_batches` start 100% empty on Day 1.

- [ ] **TASK-003: Basket Co-Purchase Sample Gating (Apriori / Lift Thresholds)**
  - Add statistical sample gating to `get_basket_co_purchases()`: require a minimum of 20–25 recorded bills before showing association rules.
  - When bills $< 25$, return an informative status: `"Accumulating basket combinations (X/25 bills recorded)"` to prevent early sample distortion.

- [ ] **TASK-004: Early Demand Forecast Extrapolation (Days 1–29 Fallback)**
  - Update `forecasting.py`: during the first 30 days of live operation, extrapolate daily average run-rate to a 30-day equivalent: `(total_qty / days_active) * 30`.
  - Prevents underpredicting next-month demand by $80\%$ during the store's initial weeks.

- [ ] **TASK-005: Preserve Canonical FMCG Catalog (V2 Migration Ground Truth)**
  - Retain `V2__seed_catalog_products.sql` as the production master dictionary for ~25 standard Indian FMCG staples (Tata Salt, Amul, Aashirvaad, Maggi, etc.).
  - Ensure dynamic auto-registration of new items remains active without corrupting existing catalog definitions.

- [ ] **TASK-006: UI Empty States & Progressive Intelligence Unlocking**
  - Update `main.py` frontend: replace raw chart canvases with graceful empty states and onboarding indicators.
  - Implement a 4-Stage Progressive Unlocking indicator:
    - **Stage 1 (Days 1–3):** Daily sales totals & top volume items.
    - **Stage 2 (Days 4–14):** Day-of-week shopping shifts & early basket pairings.
    - **Stage 3 (Days 15–30):** Extrapolated next-month forecast & weather sensitivities.
    - **Stage 4 (Day 31+):** Full month-over-month momentum & surge acceleration.
