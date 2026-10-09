import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from seed_data import seed_database
from analytics import (
    get_basket_co_purchases,
    get_day_of_week_patterns,
    get_time_of_day_patterns,
    get_weather_impact_analysis,
    get_changing_trend_patterns,
    get_historical_monthly_summary
)
from forecasting import (
    get_next_month_forecast,
    get_seasonal_and_festival_roadmap
)
from ingestion import ingest_gemini_sales_json
from gemini_enricher import enrich_analytics_with_gemini

app = FastAPI(title="Kirana Demand Pattern & Predictive Forecasting", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    # TASK-002: In production, tables start clean on Day 1 unless synthetic seed is explicitly allowed
    if os.getenv("ALLOW_SYNTHETIC_SEED", "false").lower() == "true":
        seed_database()

# --- API Routes ---

@app.get("/api/basket-patterns")
def api_basket_patterns():
    return get_basket_co_purchases()

@app.get("/api/day-patterns")
def api_day_patterns():
    return get_day_of_week_patterns()

@app.get("/api/time-patterns")
def api_time_patterns():
    return get_time_of_day_patterns()

@app.get("/api/weather-patterns")
def api_weather_patterns():
    return get_weather_impact_analysis()

@app.get("/api/changing-trends")
def api_changing_trends():
    return get_changing_trend_patterns()

@app.get("/api/monthly-history")
def api_monthly_history():
    return get_historical_monthly_summary()

@app.get("/api/next-month-forecast")
def api_next_month_forecast():
    return get_next_month_forecast()

@app.get("/api/festival-roadmap")
def api_festival_roadmap():
    return get_seasonal_and_festival_roadmap()

@app.get("/api/ai-insights")
def api_ai_insights():
    try:
        return enrich_analytics_with_gemini(force_refresh=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-insights/refresh")
def api_ai_insights_refresh():
    try:
        return enrich_analytics_with_gemini(force_refresh=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/festival-trend/crawl")
def api_crawl_festival_trend(festival: str, year: Optional[int] = None):
    try:
        from festival_trend_crawler import crawl_and_update_festival_trend
        target_year = year or datetime.now().year
        res = crawl_and_update_festival_trend(festival, target_year, force=True)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
def api_ingest(payload: Dict[str, Any]):
    try:
        result = ingest_gemini_sales_json(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reset-data")
def api_reset():
    seed_database()
    return {"status": "success", "message": "Historical data re-initialized."}

# --- Dashboard UI ---
@app.get("/", response_class=HTMLResponse)
def index_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kirana Demand & Pattern Forecasting</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0f172a; }
  </style>
</head>
<body class="text-slate-100 antialiased min-h-screen pb-16">

  <!-- Header -->
  <header class="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap justify-between items-center gap-3">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-400 font-extrabold text-xl shadow-inner">
          📊
        </div>
        <div>
          <h1 class="text-lg sm:text-xl font-bold tracking-tight flex items-center gap-2 text-white">
            Kirana Demand & Buying Patterns
            <span class="text-xs bg-indigo-500 text-white font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">Predictive AI</span>
          </h1>
          <p class="text-xs text-slate-400">Basket Associations • Weather & Festival Impacts • Multi-Season Forecasting</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button onclick="openIngestModal()" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-md flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Ingest Gemini Notepad JSON
        </button>
        <button onclick="loadAll()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-xl text-xs transition-colors border border-slate-700" title="Refresh">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">

    <!-- Progressive Intelligence Unlocking Banner (TASK-006) -->
    <div class="bg-slate-900/90 rounded-2xl p-4 border border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-lg">
          🔓
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-white uppercase tracking-wider">Store Maturity & Progressive Intelligence</span>
            <span id="stage-badge" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
              Stage: Checking...
            </span>
          </div>
          <p id="stage-desc" class="text-[11px] text-slate-400 mt-0.5">
            Progressively unlocks deeper statistical models as transaction history accumulates.
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2 text-xs">
        <div class="flex items-center gap-1.5" id="stage-steps">
          <span id="step-1" class="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 text-slate-400" title="Days 1-3">1: Volume</span>
          <span class="text-slate-600">→</span>
          <span id="step-2" class="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 text-slate-400" title="Days 4-14">2: Baskets</span>
          <span class="text-slate-600">→</span>
          <span id="step-3" class="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 text-slate-400" title="Days 15-30">3: Forecast</span>
          <span class="text-slate-600">→</span>
          <span id="step-4" class="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 text-slate-400" title="Days 31+">4: Momentum</span>
        </div>
      </div>
    </div>

    <!-- KPI Summary Row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Next Month Projected Demand</span>
        <div class="mt-2 text-2xl font-black text-indigo-400" id="kpi-projected-rev">₹0</div>
        <span class="text-xs text-slate-400 font-medium" id="kpi-target-month">Target Month Forecast</span>
      </div>
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fastest Surging Item</span>
        <div class="mt-2 text-xl font-black text-emerald-400 truncate" id="kpi-top-surge">-</div>
        <span class="text-xs text-emerald-500 font-semibold" id="kpi-surge-rate">+0% Growth Momentum</span>
      </div>
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top Basket Co-Purchase</span>
        <div class="mt-2 text-base font-bold text-amber-300 truncate" id="kpi-top-pair">-</div>
        <span class="text-xs text-slate-400 font-medium" id="kpi-pair-stat">0% Co-Purchase Frequency</span>
      </div>
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Next Festival / Surge Event</span>
        <div class="mt-2 text-lg font-black text-rose-400 truncate" id="kpi-next-fest">-</div>
        <span class="text-xs text-rose-300 font-semibold" id="kpi-fest-days">0 Days Remaining</span>
      </div>
    </div>

    <!-- ✨ Gemini AI Retail Strategy Advisor Section -->
    <div class="bg-gradient-to-br from-purple-950/50 via-slate-900 to-slate-900 border border-purple-800/40 rounded-3xl p-5 sm:p-6 shadow-xl relative overflow-hidden">
      <!-- Ambient background glow -->
      <div class="absolute -right-16 -top-16 w-56 h-56 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <!-- Advisor Header -->
      <div class="flex flex-wrap justify-between items-start gap-4 mb-5 relative z-10">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="flex h-3 w-3 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
            </span>
            <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              ✨ Gemini AI Retail Strategy Advisor
              <span id="ai-model-badge" class="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 uppercase tracking-wider">
                Loading...
              </span>
            </h2>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            Autonomous FMCG intelligence synthesizing basket co-purchases, weather spikes, distributor timing & SKU momentum
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span id="ai-last-cached" class="text-[11px] text-slate-400 font-medium">Synced: --</span>
          <button id="ai-refresh-btn" onclick="triggerManualAiRefresh()" class="bg-purple-600 hover:bg-purple-500 text-white font-bold px-3.5 py-2 rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5 active:scale-95 disabled:opacity-50">
            <svg id="ai-refresh-icon" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            <span id="ai-refresh-text">⚡ Re-Synthesize Strategy</span>
          </button>
        </div>
      </div>

      <!-- Top Row: Executive Brief & Tactical Weather Directive -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5 relative z-10">
        <!-- Executive Brief -->
        <div class="lg:col-span-2 bg-slate-950/70 border border-purple-900/30 rounded-2xl p-4 flex flex-col justify-between">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-300 shrink-0 text-lg shadow-inner">
              🧠
            </div>
            <div>
              <span class="text-[11px] font-bold uppercase tracking-wider text-purple-400">Daily Executive Strategy Brief</span>
              <p id="ai-exec-summary" class="text-xs text-slate-200 mt-1.5 leading-relaxed font-normal">
                Synthesizing retail strategic advice from store patterns...
              </p>
            </div>
          </div>
        </div>

        <!-- Weather Tactical Directive -->
        <div class="bg-slate-950/70 border border-sky-900/30 rounded-2xl p-4 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1">
                ⛅ Weather Directive
              </span>
              <span id="ai-weather-headline" class="text-[10px] font-semibold text-slate-300 bg-sky-950/60 px-2 py-0.5 rounded-full border border-sky-800/40 truncate max-w-[140px]">-</span>
            </div>
            <p id="ai-weather-directive" class="text-xs text-slate-300 leading-snug">
              Analyzing current weather correlations...
            </p>
          </div>
          <div class="mt-2.5 pt-2 border-t border-slate-800/80">
            <span class="text-[10px] text-slate-500 font-semibold block mb-1 uppercase tracking-wider">Priority Counter SKUs:</span>
            <div id="ai-weather-items" class="flex flex-wrap gap-1">
              <span class="text-[10px] text-slate-400">Loading...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- High-ROI Merchandising Combos (Grid) -->
      <div class="mb-5 relative z-10">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
            🎯 AI Merchandising Combos & Placement Directives
          </h3>
          <span class="text-[11px] text-slate-400">Actionable layout for 150-300 sq.ft. Kirana formats</span>
        </div>
        <div id="ai-combos-container" class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div class="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-500 text-center">Loading AI merchandising combos...</div>
        </div>
      </div>

      <!-- 2-Col: Distributor Procurement & Trend Context -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 relative z-10">
        <!-- Distributor Procurement Advice -->
        <div class="bg-slate-950/70 border border-amber-900/30 rounded-2xl p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
              📦 Distributor Procurement & Timing Tips
            </h3>
            <span class="text-[10px] text-slate-400">Lead times & price surge alerts</span>
          </div>
          <div id="ai-procurement-container" class="space-y-2.5">
            <div class="text-xs text-slate-500 p-2">Loading procurement tips...</div>
          </div>
        </div>

        <!-- Why-Behind-The-Trend Intelligence -->
        <div class="bg-slate-950/70 border border-indigo-900/30 rounded-2xl p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
              🔍 "Why-Behind-The-Trend" FMCG Context
            </h3>
            <span class="text-[10px] text-slate-400">Real-world neighborhood drivers</span>
          </div>
          <div id="ai-trends-container" class="space-y-2.5">
            <div class="text-xs text-slate-500 p-2">Loading trend explanations...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 1: Next Month SKU Demand Forecast -->
    <div class="bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-900/50 rounded-2xl p-5 shadow-lg">
      <div class="flex flex-wrap justify-between items-center gap-3 mb-4">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-indigo-500 animate-pulse"></span>
            Next Month Predictive Demand Forecast
          </h2>
          <p class="text-xs text-slate-400" id="forecast-header-sub">Projected unit volume based on recent velocity + momentum + upcoming seasonal weighting</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs px-3 py-1 rounded-full font-bold" id="forecast-season-badge">Season: Loading...</span>
        </div>
      </div>

      <div class="overflow-x-auto max-h-80">
        <table class="w-full text-left text-xs bg-slate-950/40 rounded-xl border border-slate-800 overflow-hidden">
          <thead class="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold sticky top-0">
            <tr>
              <th class="py-2.5 px-3">Product Name</th>
              <th class="py-2.5 px-3">Category</th>
              <th class="py-2.5 px-3">Recent 30D Sold</th>
              <th class="py-2.5 px-3 text-indigo-300">Projected Next Month</th>
              <th class="py-2.5 px-3">Growth Shift</th>
              <th class="py-2.5 px-3">Est. Next Month Rev</th>
              <th class="py-2.5 px-3">Stocking Directive</th>
            </tr>
          </thead>
          <tbody id="forecast-table-body" class="divide-y divide-slate-800 text-slate-200">
            <tr><td colspan="7" class="py-4 text-center text-slate-500">Calculating projections...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Section 2: Buying Patterns & Weather Impacts -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Co-Purchasing Habits (Basket Pairs) -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm flex flex-col justify-between">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
            <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
            Customer Basket Co-Purchases
          </h2>
          <p class="text-xs text-slate-400 mb-3">Grouped via your notepad's <strong>sale no.</strong> column</p>
          <div id="basket-pair-list" class="space-y-2 max-h-96 overflow-y-auto">
            <div class="text-center py-6 text-slate-500 text-xs">Mining basket combinations...</div>
          </div>
        </div>
      </div>

      <!-- Weather Impact Insights -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm flex flex-col justify-between">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
            <svg class="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
            Weather Demand Correlations
          </h2>
          <p class="text-xs text-slate-400 mb-3">Derived from the notepad's <strong>weather</strong> column</p>
          <div id="weather-insights-list" class="space-y-2 text-xs max-h-96 overflow-y-auto">
            <!-- Filled via JS -->
          </div>
        </div>
      </div>

      <!-- Day of the Week Buying Shifts -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
          <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          Day-of-Week Shopping Behavior
        </h2>
        <p class="text-xs text-slate-400 mb-3">Weekday essentials vs. Weekend surge</p>
        <div id="day-pattern-list" class="space-y-1.5 text-xs max-h-96 overflow-y-auto">
          <!-- Filled via JS -->
        </div>
      </div>
    </div>

    <!-- Section 3: Changing Trends (Surging vs Declining) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-emerald-900/40 shadow-sm">
        <h2 class="text-sm font-bold text-emerald-400 flex items-center gap-2 mb-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
          Surging Products (Fastest Momentum Acceleration)
        </h2>
        <p class="text-xs text-slate-400 mb-3">Recent 30 days vs prior 30 days</p>
        <div id="surging-container" class="space-y-2 text-xs">
          <!-- Filled via JS -->
        </div>
      </div>

      <div class="bg-slate-900/90 rounded-2xl p-5 border border-rose-900/40 shadow-sm">
        <h2 class="text-sm font-bold text-rose-400 flex items-center gap-2 mb-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"/></svg>
          Declining Products (Cooling Down / Preference Shift)
        </h2>
        <p class="text-xs text-slate-400 mb-3">Items slowing down in sales frequency</p>
        <div id="declining-container" class="space-y-2 text-xs">
          <!-- Filled via JS -->
        </div>
      </div>
    </div>

    <!-- Monthly Multi-Month Trend Chart -->
    <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
      <h2 class="text-base font-bold text-white mb-1">Historical Monthly Volume & Basket Size Progression</h2>
      <p class="text-xs text-slate-400 mb-4">Past 6 months customer demand and average spend per visit (₹)</p>
      <div class="h-64">
        <canvas id="monthlyChart"></canvas>
      </div>
    </div>

    <!-- Section 4: Indian Festival Surge Calendar -->
    <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
      <div class="flex justify-between items-center mb-3">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            🪔 Indian Festive & Seasonal Surge Roadmap (Next 12 Months)
          </h2>
          <p class="text-xs text-slate-400">Derived from calendar & your notepad's <strong>festival</strong> annotations</p>
        </div>
      </div>

      <div id="festivals-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        <!-- Filled via JS -->
      </div>
    </div>

  </main>

  <!-- Ingest Modal -->
  <div id="ingestModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
      <div class="flex justify-between items-center">
        <div>
          <h3 class="text-lg font-bold text-white">Ingest Gemini Daily Notepad JSON</h3>
          <p class="text-xs text-slate-400">Structured table format: [sale no.] [time] [products] [total] [weather] [festival]</p>
        </div>
        <button onclick="closeIngestModal()" class="text-slate-400 hover:text-white text-xl font-bold">&times;</button>
      </div>

      <div>
        <div class="flex justify-between items-center mb-1">
          <label class="text-xs font-semibold text-slate-300">JSON Payload</label>
          <button onclick="loadSamplePayload()" class="text-xs text-indigo-400 hover:underline font-semibold">Load Sample Notepad JSON</button>
        </div>
        <textarea id="jsonInput" rows="10" class="w-full bg-slate-950 font-mono text-xs p-3 border border-slate-800 rounded-xl text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
      </div>

      <div id="ingestStatus" class="text-xs font-semibold hidden"></div>

      <div class="flex justify-end gap-2 pt-2">
        <button onclick="closeIngestModal()" class="px-4 py-2 text-xs font-bold text-slate-400 hover:bg-slate-800 rounded-xl transition-colors">Cancel</button>
        <button onclick="submitJson()" id="ingestBtn" class="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-md transition-all">Ingest & Update Patterns</button>
      </div>
    </div>
  </div>

  <script>
    let monthlyChartInstance = null;

    async function fetchAPI(url) {
      try {
        const res = await fetch(url);
        return await res.json();
      } catch (e) {
        console.error("Fetch error:", url, e);
        return null;
      }
    }

    async function loadAll() {
      // 1. Next Month Forecast
      const forecast = await fetchAPI('/api/next-month-forecast');
      if (forecast) {
        updateProgressiveUnlock(forecast.active_days || 0);

        document.getElementById('kpi-projected-rev').innerText = '₹' + (forecast.total_projected_revenue || 0).toLocaleString('en-IN');
        document.getElementById('kpi-target-month').innerText = forecast.target_month + ' Forecast';
        document.getElementById('forecast-header-sub').innerText = forecast.is_extrapolated 
          ? `Early Run-Rate Extrapolated for ${forecast.target_month} (${forecast.target_season} Season) from ${forecast.active_days} active days.`
          : `Projected for ${forecast.target_month} (${forecast.target_season} Season) across ${(forecast.forecast_items || []).length} key items.`;
        document.getElementById('forecast-season-badge').innerText = `Upcoming Season: ${forecast.target_season}${forecast.is_extrapolated ? ' (Extrapolated)' : ''}`;

        const tbody = document.getElementById('forecast-table-body');
        if (forecast.is_cold_start || !forecast.forecast_items || forecast.forecast_items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">
            <div class="inline-flex flex-col items-center gap-2">
              <span class="text-2xl">🌱</span>
              <span class="font-bold text-white text-xs">Cold-Start Mode Active</span>
              <span class="text-[11px] text-slate-500 max-w-md">No sales transactions recorded yet. Ingest your first daily sales notepad to activate run-rate predictive demand forecasting.</span>
            </div>
          </td></tr>`;
        } else {
          tbody.innerHTML = forecast.forecast_items.map(item => `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 px-3 font-semibold text-white">${item.name}</td>
              <td class="py-2.5 px-3 text-slate-400">${item.category}</td>
              <td class="py-2.5 px-3 text-slate-300">${item.current_month_qty} ${item.unit}</td>
              <td class="py-2.5 px-3 font-bold text-indigo-300">${item.projected_next_month_qty} ${item.unit}</td>
              <td class="py-2.5 px-3 font-bold ${item.growth_trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                ${item.growth_trend >= 0 ? '+' : ''}${item.growth_trend}%
              </td>
              <td class="py-2.5 px-3 font-bold text-slate-200">₹${item.projected_revenue.toLocaleString('en-IN')}</td>
              <td class="py-2.5 px-3 text-slate-400 text-[11px]">${item.stocking_action}</td>
            </tr>
          `).join('');
        }
      }

      // 2. Basket Co-Purchases
      const basketData = await fetchAPI('/api/basket-patterns');
      const basketContainer = document.getElementById('basket-pair-list');
      if (basketData && basketData.is_gated) {
        document.getElementById('kpi-top-pair').innerText = 'Accumulating';
        document.getElementById('kpi-pair-stat').innerText = `${basketData.recorded_bills}/${basketData.threshold_bills} Bills Recorded`;
        basketContainer.innerHTML = `
          <div class="text-center py-6 text-indigo-300 text-xs font-semibold bg-slate-950/40 rounded-xl p-3 border border-indigo-900/30">
            📊 ${basketData.message}
            <p class="text-[10px] text-slate-500 mt-1 font-normal">Need 25 bills to avoid statistical skew in co-purchase lift.</p>
          </div>`;
      } else {
        const pairs = Array.isArray(basketData) ? basketData : (basketData ? (basketData.patterns || []) : []);
        if (pairs.length > 0) {
          document.getElementById('kpi-top-pair').innerText = `${pairs[0].item_a} + ${pairs[0].item_b}`;
          document.getElementById('kpi-pair-stat').innerText = `${pairs[0].confidence_pct}% Co-Purchase Rate`;

          basketContainer.innerHTML = pairs.map(b => `
            <div class="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800">
              <div class="flex justify-between items-start gap-1">
                <div class="font-bold text-slate-200 text-xs flex items-center gap-1">
                  <span class="text-indigo-400">${b.item_a}</span>
                  <span class="text-slate-500">+</span>
                  <span class="text-indigo-400">${b.item_b}</span>
                </div>
                <span class="bg-indigo-500/20 text-indigo-300 text-[10px] font-bold px-1.5 py-0.5 rounded-full border border-indigo-500/30">
                  ${b.confidence_pct}%
                </span>
              </div>
              <p class="text-[10px] text-slate-400 mt-1">${b.insight}</p>
            </div>
          `).join('');
        } else {
          basketContainer.innerHTML = `<div class="text-center py-6 text-slate-500 text-xs">No basket pairings recorded yet.</div>`;
        }
      }

      // 3. Weather Insights
      const weatherData = await fetchAPI('/api/weather-patterns');
      if (weatherData) {
        const wContainer = document.getElementById('weather-insights-list');
        wContainer.innerHTML = weatherData.map(w => `
          <div class="p-2.5 bg-slate-950/60 border border-sky-950/40 rounded-xl">
            <div class="flex justify-between items-center mb-1">
              <span class="font-bold text-sky-400 text-xs">${w.weather} Weather (${w.days_observed} days)</span>
            </div>
            <p class="text-[10px] text-slate-400">${w.behavior_theme}</p>
            <div class="mt-1 flex flex-wrap gap-1">
              ${w.top_products.map(p => `
                <span class="bg-slate-800 text-slate-300 text-[10px] px-1.5 py-0.5 rounded">
                  ${p.product_name} (~${p.avg_daily_qty}/day)
                </span>
              `).join('')}
            </div>
          </div>
        `).join('');
      }

      // 4. Day of Week Patterns
      const dayData = await fetchAPI('/api/day-patterns');
      if (dayData) {
        const dContainer = document.getElementById('day-pattern-list');
        dContainer.innerHTML = dayData.map(d => `
          <div class="p-2 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
            <div>
              <span class="font-bold text-white text-xs">${d.day}</span>
              <p class="text-[10px] text-slate-400">${d.pattern_theme}</p>
            </div>
            <div class="text-right">
              <span class="font-bold text-slate-200">₹${d.avg_basket_value}</span>
              <p class="text-[9px] text-slate-500">avg spend</p>
            </div>
          </div>
        `).join('');
      }

      // 5. Changing Trends
      const trends = await fetchAPI('/api/changing-trends');
      if (trends) {
        if (trends.surging_products.length > 0) {
          document.getElementById('kpi-top-surge').innerText = trends.surging_products[0].product_name;
          document.getElementById('kpi-surge-rate').innerText = `+${trends.surging_products[0].growth_pct}% 30D Acceleration`;

          document.getElementById('surging-container').innerHTML = trends.surging_products.map(s => `
            <div class="p-2.5 bg-slate-950/60 border border-emerald-900/30 rounded-xl flex justify-between items-center">
              <div>
                <span class="font-bold text-white">${s.product_name}</span>
                <p class="text-[11px] text-slate-400">${s.category} • ${s.recent_30d_qty} units (vs ${s.prior_30d_qty} prior)</p>
              </div>
              <span class="text-xs font-black text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded-md border border-emerald-800/40">
                +${s.growth_pct}%
              </span>
            </div>
          `).join('');
        }

        if (trends.declining_products.length > 0) {
          document.getElementById('declining-container').innerHTML = trends.declining_products.map(d => `
            <div class="p-2.5 bg-slate-950/60 border border-rose-900/30 rounded-xl flex justify-between items-center">
              <div>
                <span class="font-bold text-white">${d.product_name}</span>
                <p class="text-[11px] text-slate-400">${d.category} • ${d.recent_30d_qty} units (vs ${d.prior_30d_qty} prior)</p>
              </div>
              <span class="text-xs font-black text-rose-400 bg-rose-950/50 px-2 py-0.5 rounded-md border border-rose-800/40">
                ${d.growth_pct}%
              </span>
            </div>
          `).join('');
        }
      }

      // 6. Monthly Timeline Chart
      const monthlyHistory = await fetchAPI('/api/monthly-history');
      if (monthlyHistory) renderMonthlyChart(monthlyHistory);

      // 7. Festival Roadmap
      const roadmapData = await fetchAPI('/api/festival-roadmap');
      if (roadmapData && roadmapData.roadmap.length > 0) {
        const nextFest = roadmapData.roadmap[0];
        document.getElementById('kpi-next-fest').innerText = nextFest.name;
        document.getElementById('kpi-fest-days').innerText = `${nextFest.days_until} Days Remaining (${nextFest.target_date})`;

        const fContainer = document.getElementById('festivals-container');
        fContainer.innerHTML = roadmapData.roadmap.map(f => {
          const isLiveWeb = f.source && (f.source.includes('DuckDuckGo') || f.source.includes('gemini'));
          return `
          <div class="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div class="flex justify-between items-start gap-2 mb-1.5">
                <h3 class="font-bold text-white text-xs">${f.name}</h3>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${f.days_until <= 30 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-slate-800 text-slate-300'}">
                  ${f.days_until} days
                </span>
              </div>
              <div class="flex items-center justify-between text-[10px] text-slate-400 mb-2">
                <span>📅 ${f.target_date}</span>
                <span class="px-1.5 py-0.2 rounded text-[9px] font-semibold ${isLiveWeb ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-800/50' : 'bg-slate-800/80 text-slate-400'}">
                  ${isLiveWeb ? '🌐 Live Web Trends' : '🏛️ Regional Gazette'}
                </span>
              </div>
              <p class="text-[10px] text-slate-500 mb-2">${f.status}</p>
              <div class="space-y-1.5 pt-2 border-t border-slate-800">
                ${f.key_items.map(k => `
                  <div class="text-[11px] text-slate-300 flex justify-between" title="${k.trend_reason || k.prep_advice || ''}">
                    <span class="truncate max-w-[170px]">${k.item}</span>
                    <span class="font-bold shrink-0 ${k.surge_pct > 0 ? 'text-amber-400' : 'text-slate-500'}">${k.surge_pct > 0 ? '+' : ''}${k.surge_pct}%</span>
                  </div>
                `).join('')}
              </div>
            </div>
            <div class="mt-3 pt-2 border-t border-slate-900 flex justify-end">
              <button onclick="crawlFestivalTrend('${encodeURIComponent(f.name)}', this)" class="text-[10px] font-semibold px-2 py-1 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-lg flex items-center gap-1 transition-all">
                <span>⚡</span> <span>Sense Live Trends</span>
              </button>
            </div>
          </div>
        `;
        }).join('');
      }

      // 8. AI Retail Strategy Advisor
      await loadAIInsights(false);
    }

    async function loadAIInsights(force = false) {
      try {
        const url = force ? '/api/ai-insights/refresh' : '/api/ai-insights';
        const method = force ? 'POST' : 'GET';
        const res = await fetch(url, { method });
        const data = await res.json();
        if (!data) return;

        // Model badge
        const modelBadge = document.getElementById('ai-model-badge');
        if (modelBadge) {
          modelBadge.innerText = data._model || 'Gemini 3.8 Flash';
          if (data._is_fallback) {
            modelBadge.innerText += ' (Offline Fallback)';
            modelBadge.className = 'text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wider';
          } else {
            modelBadge.className = 'text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 uppercase tracking-wider';
          }
        }

        // Cache timestamp
        const lastCached = document.getElementById('ai-last-cached');
        if (lastCached && data._cached_at) {
          const dt = new Date(data._cached_at);
          lastCached.innerText = 'Synced: ' + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        // Executive brief
        const execSummary = document.getElementById('ai-exec-summary');
        if (execSummary && data.daily_executive_summary) {
          execSummary.innerText = data.daily_executive_summary;
        }

        // Weather directive
        if (data.weather_tactical_action) {
          const wHeadline = document.getElementById('ai-weather-headline');
          if (wHeadline) wHeadline.innerText = data.weather_tactical_action.headline || 'Action Alert';
          const wDirective = document.getElementById('ai-weather-directive');
          if (wDirective) wDirective.innerText = data.weather_tactical_action.action_directive || '';
          const wItems = document.getElementById('ai-weather-items');
          if (wItems && Array.isArray(data.weather_tactical_action.priority_items)) {
            wItems.innerHTML = data.weather_tactical_action.priority_items.map(item => `
              <span class="bg-sky-950/70 border border-sky-800/40 text-sky-300 text-[10px] font-semibold px-2 py-0.5 rounded-md">${item}</span>
            `).join('');
          }
        }

        // Merchandising combos
        const combosContainer = document.getElementById('ai-combos-container');
        if (combosContainer && Array.isArray(data.merchandising_combos) && data.merchandising_combos.length > 0) {
          combosContainer.innerHTML = data.merchandising_combos.map(c => `
            <div class="p-3.5 bg-slate-950/70 rounded-2xl border border-purple-900/30 flex flex-col justify-between hover:border-purple-600/40 transition-all">
              <div>
                <div class="flex items-start justify-between gap-1 mb-2">
                  <span class="font-bold text-xs text-purple-300">${c.combo_name}</span>
                  <span class="bg-purple-500/20 text-purple-200 text-[10px] font-bold px-2 py-0.5 rounded-full border border-purple-500/30 shrink-0">Promo Deal</span>
                </div>
                <div class="text-[11px] font-semibold text-slate-200 mb-1.5 flex items-center gap-1.5">
                  <span>🛒</span>
                  <span class="text-white">${c.items}</span>
                </div>
                <p class="text-[11px] text-slate-400 mb-2 leading-relaxed">${c.consumer_behavior}</p>
              </div>
              <div class="pt-2 border-t border-slate-800/80 space-y-1">
                <div class="text-[10px] text-amber-300 font-semibold flex items-center gap-1">
                  <span>🏷️</span> <span>${c.suggested_promo}</span>
                </div>
                <div class="text-[10px] text-slate-400 flex items-center gap-1">
                  <span>📍</span> <span>${c.shelf_placement_directive}</span>
                </div>
              </div>
            </div>
          `).join('');
        }

        // Procurement advice
        const procContainer = document.getElementById('ai-procurement-container');
        if (procContainer && Array.isArray(data.procurement_distributor_advice) && data.procurement_distributor_advice.length > 0) {
          procContainer.innerHTML = data.procurement_distributor_advice.map(p => `
            <div class="p-2.5 bg-slate-900/60 rounded-xl border border-amber-950/40">
              <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-xs text-white">${p.product}</span>
                <span class="text-[10px] text-amber-300 font-bold bg-amber-950/60 px-2 py-0.5 rounded-full border border-amber-800/40">Distributor Tip</span>
              </div>
              <p class="text-[11px] text-slate-200 font-medium mb-1">${p.recommended_action}</p>
              <p class="text-[10px] text-slate-400 italic">💡 ${p.distributor_timing_tip}</p>
            </div>
          `).join('');
        }

        // Trend insights
        const trendsContainer = document.getElementById('ai-trends-container');
        if (trendsContainer && Array.isArray(data.trend_insights) && data.trend_insights.length > 0) {
          trendsContainer.innerHTML = data.trend_insights.map(t => {
            const isSurge = (t.trend_direction || '').toLowerCase().includes('surge') || (t.momentum || '').startsWith('+');
            return `
              <div class="p-2.5 bg-slate-900/60 rounded-xl border ${isSurge ? 'border-emerald-950/40' : 'border-rose-950/40'}">
                <div class="flex items-center justify-between mb-1">
                  <span class="font-bold text-xs text-white">${t.product}</span>
                  <span class="text-[10px] font-black px-2 py-0.5 rounded-md ${isSurge ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-800/40' : 'text-rose-400 bg-rose-950/60 border border-rose-800/40'}">
                    ${t.trend_direction} (${t.momentum})
                  </span>
                </div>
                <p class="text-[11px] text-slate-300 leading-snug">${t.retail_explanation}</p>
              </div>
            `;
          }).join('');
        }

      } catch (err) {
        console.error("AI Insights load failed:", err);
      }
    }

    async function triggerManualAiRefresh() {
      const btn = document.getElementById('ai-refresh-btn');
      const icon = document.getElementById('ai-refresh-icon');
      const text = document.getElementById('ai-refresh-text');

      if (btn) btn.disabled = true;
      if (icon) icon.classList.add('animate-spin');
      if (text) text.innerText = 'Consulting Gemini...';

      try {
        await loadAIInsights(true);
      } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove('animate-spin');
        if (text) text.innerText = '⚡ Re-Synthesize Strategy';
      }
    }

    async function crawlFestivalTrend(encodedName, btn) {
      const festName = decodeURIComponent(encodedName);
      const origHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="animate-spin">⏳</span> <span>Searching DuckDuckGo...</span>`;
      try {
        const res = await fetch(`/api/festival-trend/crawl?festival=${encodeURIComponent(festName)}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          btn.innerHTML = `<span>✅</span> <span>Updated!</span>`;
          setTimeout(async () => {
            await loadDashboard();
          }, 800);
        } else {
          btn.innerHTML = origHtml;
          btn.disabled = false;
          alert('Trend crawl failed: ' + (data.detail || 'Error'));
        }
      } catch (err) {
        btn.innerHTML = origHtml;
        btn.disabled = false;
        alert('Crawl error: ' + err.message);
      }
    }

    function renderMonthlyChart(data) {
      const ctx = document.getElementById('monthlyChart').getContext('2d');
      if (monthlyChartInstance) monthlyChartInstance.destroy();

      monthlyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.map(d => d.month_str),
          datasets: [
            {
              type: 'line',
              label: 'Avg Basket Spend (₹)',
              data: data.map(d => d.avg_basket_value),
              borderColor: '#f59e0b',
              borderWidth: 2.5,
              yAxisID: 'y1',
              tension: 0.3
            },
            {
              label: 'Monthly Units Sold',
              data: data.map(d => d.total_units),
              backgroundColor: '#6366f1',
              borderRadius: 6,
              yAxisID: 'y'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
          scales: {
            y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
            y1: { position: 'right', grid: { display: false }, ticks: { color: '#f59e0b' } },
            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
          }
        }
      });
    }

    function openIngestModal() {
      document.getElementById('ingestModal').classList.remove('hidden');
      document.getElementById('ingestStatus').classList.add('hidden');
    }

    function closeIngestModal() {
      document.getElementById('ingestModal').classList.add('hidden');
    }

    function loadSamplePayload() {
      const sample = {
        "date": new Date().toISOString().slice(0, 10),
        "day_weather": "Rainy",
        "day_festival": "None",
        "sales": [
          {
            "sale_no": 1,
            "time": "08:15 AM",
            "time_period": "Morning",
            "bill_total": 69.0,
            "weather": "Rainy",
            "festival": "None",
            "items": [
              {"raw_text": "2 amul taaza 500", "standardized_name": "Amul Taaza Milk 500ml", "category": "Dairy", "quantity": 2, "unit": "packet", "pack_size": "500ml", "unit_price": 27.0, "line_total": 54.0},
              {"raw_text": "1 marie gold 120g", "standardized_name": "Britannia Marie Gold 120g", "category": "Snacks", "quantity": 1, "unit": "packet", "pack_size": "120g", "unit_price": 15.0, "line_total": 15.0}
            ]
          },
          {
            "sale_no": 2,
            "time": "05:30 PM",
            "time_period": "Evening",
            "bill_total": 82.0,
            "weather": "Rainy",
            "festival": "None",
            "items": [
              {"raw_text": "3 maggi packet", "standardized_name": "Maggi 2-Minute Noodles 70g", "category": "Snacks", "quantity": 3, "unit": "packet", "pack_size": "70g", "unit_price": 14.0, "line_total": 42.0},
              {"raw_text": "2 thumsup 250ml", "standardized_name": "Thums Up 250ml Bottle", "category": "Beverages", "quantity": 2, "unit": "bottle", "pack_size": "250ml", "unit_price": 20.0, "line_total": 40.0}
            ]
          },
          {
            "sale_no": 3,
            "time": "07:45 PM",
            "time_period": "Evening",
            "bill_total": 330.0,
            "weather": "Rainy",
            "festival": "None",
            "items": [
              {"raw_text": "1 aashirvaad 5k", "standardized_name": "Aashirvaad Atta 5kg", "category": "Staples", "quantity": 1, "unit": "packet", "pack_size": "5kg", "unit_price": 240.0, "line_total": 240.0},
              {"raw_text": "cheeni 2kg 90", "standardized_name": "Sugar (Loose)", "category": "Staples", "quantity": 2, "unit": "kg", "pack_size": "Loose", "unit_price": 45.0, "line_total": 90.0}
            ]
          }
        ]
      };
      document.getElementById('jsonInput').value = JSON.stringify(sample, null, 2);
    }

    async function submitJson() {
      const text = document.getElementById('jsonInput').value.trim();
      const statusEl = document.getElementById('ingestStatus');
      const btn = document.getElementById('ingestBtn');

      if (!text) {
        alert("Please paste JSON first.");
        return;
      }

      let payload;
      try {
        payload = JSON.parse(text);
      } catch (err) {
        statusEl.className = "text-xs font-semibold text-rose-400 block";
        statusEl.innerText = "Invalid JSON: " + err.message;
        return;
      }

      btn.disabled = true;
      btn.innerText = "Ingesting...";

      try {
        const res = await fetch('/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
          statusEl.className = "text-xs font-semibold text-emerald-400 block";
          statusEl.innerText = `Ingested ${data.data.sales_recorded} sales bills (${data.data.total_items_processed} items)! Refreshing patterns...`;
          setTimeout(() => {
            closeIngestModal();
            loadAll();
          }, 1200);
        } else {
          statusEl.className = "text-xs font-semibold text-rose-400 block";
          statusEl.innerText = "Error: " + (data.detail || "Failed to ingest");
        }
      } catch (e) {
        statusEl.className = "text-xs font-semibold text-rose-400 block";
        statusEl.innerText = "Network Error: " + e.message;
      } finally {
        btn.disabled = false;
        btn.innerText = "Ingest & Update Patterns";
      }
    }

    function updateProgressiveUnlock(activeDays) {
      const badge = document.getElementById('stage-badge');
      const desc = document.getElementById('stage-desc');
      const s1 = document.getElementById('step-1');
      const s2 = document.getElementById('step-2');
      const s3 = document.getElementById('step-3');
      const s4 = document.getElementById('step-4');

      [s1, s2, s3, s4].forEach(s => {
        if (s) s.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 text-slate-400';
      });

      if (activeDays <= 3) {
        if (badge) badge.innerText = `Stage 1 (${activeDays}/3 Days)`;
        if (desc) desc.innerText = 'Stage 1 Active: Capturing baseline daily sales volume and top velocity SKUs.';
        if (s1) s1.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-600 text-white';
      } else if (activeDays <= 14) {
        if (badge) badge.innerText = `Stage 2 (${activeDays}/14 Days)`;
        if (desc) desc.innerText = 'Stage 2 Active: Unlocking day-of-week shopping shifts and customer basket co-purchases.';
        if (s1) s1.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-600 text-white';
        if (s2) s2.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-600 text-white';
      } else if (activeDays <= 30) {
        if (badge) badge.innerText = `Stage 3 (${activeDays}/30 Days)`;
        if (desc) desc.innerText = 'Stage 3 Active: Early run-rate extrapolation active for next-month forecast and weather lifts.';
        [s1, s2].forEach(s => { if (s) s.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-600 text-white'; });
        if (s3) s3.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-600 text-white';
      } else {
        if (badge) badge.innerText = `Stage 4 Mature (${activeDays}+ Days)`;
        if (desc) desc.innerText = 'Stage 4 Fully Mature: Complete month-over-month trend momentum and multi-season forecasting active.';
        [s1, s2, s3, s4].forEach(s => { if (s) s.className = 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-600 text-white'; });
      }
    }

    window.addEventListener('DOMContentLoaded', loadAll);
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
