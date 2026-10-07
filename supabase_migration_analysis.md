# Supabase Persistent Database Migration Analysis
### Failsafe Architecture, Data Integrity & Versioned Migrations (Flyway Pattern)

---

## 1. Executive Overview

This analysis outlines the strategy to migrate the **Kirana Demand Pattern & Forecasting System** from local SQLite to **Supabase (PostgreSQL)**, adhering to strict data integrity, failsafe error handling, and Flyway-style versioned DDL/DML migrations.

```mermaid
flowchart TD
    subgraph Local_App["Kirana Application Backend"]
        M1["Flyway-Style Migration Runner"] -->|Applies V*.sql| PG[("Supabase PostgreSQL")]
        API["FastAPI Ingestion / Analytics"] -->|Pooled Connection| PG
        API -.->|Offline / Network Failure| FB["Local SQLite Failsafe Buffer"]
        FB -.->|Auto-Replay on Reconnect| PG
    end

    subgraph Supabase_Cloud["Supabase Cloud Infrastructure"]
        PG --> T1["schema_version (Audit Table)"]
        PG --> T2["catalog_items (Master Data)"]
        PG --> T3["sales_batches & sale_items (Time-Series)"]
    end
```

---

## 2. Flyway-Style Versioned Migration Architecture

To maintain deterministic schema evolution without manual database dashboard tampering, we implement a Flyway-compatible versioning pattern:

### 2.1 File Naming & Directory Convention
```
kirana-analytics/
└── migrations/
    ├── V1__initial_schema.sql         # DDL: Tables, constraints, indexes
    ├── V2__seed_catalog_products.sql  # DML: Master product catalog & aliases
    ├── V3__analytics_views.sql        # DDL: Pre-computed aggregation views
    └── migration_runner.py            # Automated executor & checksum verifier
```

### 2.2 Schema Audit Table (`schema_version`)
Each execution inspects or creates a version tracker:
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    installed_rank SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'SQL'
    script VARCHAR(1000) NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA-256 hash of script content
    installed_by VARCHAR(100) NOT NULL,
    installed_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL
);
```

### 2.3 Migration Integrity Guarantees
- **Transactional DDL:** PostgreSQL supports transactional DDL. Each migration script runs inside a single `BEGIN ... COMMIT` block; any syntax or constraint error triggers an instant `ROLLBACK`.
- **Checksum Verification:** Scripts are hashed with SHA-256. If an already-applied migration script is altered locally, the runner halts with a checksum mismatch exception to protect production integrity.
- **Idempotency:** Re-running the application simply skips already-applied versions.

---

## 3. Data Integrity & PostgreSQL Constraints

Transitioning to Supabase PostgreSQL elevates schema robustness with production constraints:

1. **Strict Foreign Keys & Cascade Guarantees:**
   - `sale_items.batch_id` references `sales_batches.id` with `ON DELETE CASCADE`.
2. **Check Constraints:**
   - `quantity > 0` and `total_amount >= 0`.
   - `time_period IN ('Morning', 'Afternoon', 'Evening', 'Night')`.
   - `weather IN ('Sunny', 'Rainy', 'Hot', 'Cold', 'Normal', 'Humid', 'Overcast', 'Pleasant')`.
3. **Optimized Indexes:**
   - Multi-column index: `(sale_date, product_name)` for lightning-fast 30-day momentum comparisons.
   - Index on `basket_id` for instant FP-Growth co-purchase pairing calculations.

---

## 4. Failsafe & Operational Resilience Strategy

A counter app in a Kirana store faces sporadic internet connectivity. We propose a **Two-Tier Resilience Strategy**:

| Threat | Mitigation |
| :--- | :--- |
| **Transient Network Drop** | Connection pooling (SQLAlchemy / asyncpg with retry backoff). |
| **Extended Internet Outage** | **Offline Failsafe Buffer:** If Supabase is unreachable, daily notepad JSON saves to a local SQLite fallback queue, then auto-replays to Supabase when connection restores. |
| **Bad Ingestion Payload** | Ingestion runs inside an explicit DB transaction—if any row fails, zero partial rows are written. |

---

## 5. Clarifications & Actions Needed From You

To proceed with this milestone, please confirm:

### Action Required:
1. **Supabase Project Credentials:**
   - We need your **PostgreSQL Connection String** from your Supabase Dashboard:
     - Go to: *Supabase Dashboard $\rightarrow$ Project Settings $\rightarrow$ Database $\rightarrow$ Connection String (URI)*.
     - Format: `postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres` (Transaction Pooler recommended).
   - Alternatively, your `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

### Clarifications Needed:
1. **Migration Runner Tool:**
   - **Option A (Recommended):** Custom lightweight Python migration runner (`migration_runner.py`). Zero extra Java/Flyway CLI installations; runs seamlessly inside the project via `python` on any machine.
   - **Option B:** External Java-based Flyway CLI or Alembic.
2. **Offline Resilience Scope:**
   - Should we implement the **hybrid offline-queue** (local SQLite buffer when Wi-Fi is down $\rightarrow$ auto-sync to Supabase), or stick to **direct cloud-only** connection for this milestone?
