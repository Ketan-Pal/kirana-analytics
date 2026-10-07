import json
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db
from seed_data import seed_database
from analytics import (
    get_basket_co_purchases,
    get_day_of_week_patterns,
    get_time_of_day_patterns,
    get_changing_trend_patterns,
    get_historical_monthly_summary
)
from forecasting import (
    get_next_month_forecast,
    get_seasonal_and_festival_roadmap
)
from ingestion import ingest_gemini_sales_json

app = FastAPI(title="Kirana Demand Pattern & Predictive Forecasting", version="2.0.0")

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
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js -->
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
          <p class="text-xs text-slate-400">Basket Associations • Trend Momentum • Multi-Season Demand Forecasting</p>
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
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Strongest Basket Pairing</span>
        <div class="mt-2 text-base font-bold text-amber-300 truncate" id="kpi-top-pair">-</div>
        <span class="text-xs text-slate-400 font-medium" id="kpi-pair-stat">0% Co-Purchase Frequency</span>
      </div>
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Next Festival / Seasonal Event</span>
        <div class="mt-2 text-lg font-black text-rose-400 truncate" id="kpi-next-fest">-</div>
        <span class="text-xs text-rose-300 font-semibold" id="kpi-fest-days">0 Days Remaining</span>
      </div>
    </div>

    <!-- Section 1: Next Month SKU-by-SKU Demand Forecast -->
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

    <!-- Section 2: Buying Patterns & Basket Dynamics -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Co-Purchasing Habits (Basket Pairs) -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm flex flex-col justify-between">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
            <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
            Customer Basket Co-Purchasing Patterns
          </h2>
          <p class="text-xs text-slate-400 mb-4">What items are bought together in the same visit (FP-Growth Lift & Confidence)</p>
          <div id="basket-pair-list" class="space-y-2.5">
            <div class="text-center py-6 text-slate-500 text-xs">Mining basket combinations...</div>
          </div>
        </div>
      </div>

      <!-- Day of the Week Buying Shifts -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
        <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
          <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          Day-of-Week Customer Shopping Behavior
        </h2>
        <p class="text-xs text-slate-400 mb-4">How shopping habits, basket value, and demands shift through the week</p>
        <div id="day-pattern-list" class="space-y-2 text-xs">
          <!-- Filled via JS -->
        </div>
      </div>
    </div>

    <!-- Section 3: Changing Trends (Past Data Analysis: Surging vs Declining) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Surging Products -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-emerald-900/40 shadow-sm">
        <h2 class="text-sm font-bold text-emerald-400 flex items-center gap-2 mb-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
          Surging Products (Fastest Demand Acceleration)
        </h2>
        <p class="text-xs text-slate-400 mb-3">Items with strong positive momentum in recent 30 days vs prior 30 days</p>
        <div id="surging-container" class="space-y-2 text-xs">
          <!-- Filled via JS -->
        </div>
      </div>

      <!-- Declining Products -->
      <div class="bg-slate-900/90 rounded-2xl p-5 border border-rose-900/40 shadow-sm">
        <h2 class="text-sm font-bold text-rose-400 flex items-center gap-2 mb-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"/></svg>
          Declining Products (Cooling Down / Preference Shift)
        </h2>
        <p class="text-xs text-slate-400 mb-3">Items slowing down in sales volume (customer taste or seasonal taper)</p>
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

    <!-- Section 4: Indian Festival & Seasonal Surge Calendar -->
    <div class="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-sm">
      <div class="flex justify-between items-center mb-3">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            🪔 Indian Festive & Seasonal Surge Roadmap (Next 12 Months)
          </h2>
          <p class="text-xs text-slate-400">Pre-empt upcoming surge windows so you can order at wholesale before distributor price hikes</p>
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
          <p class="text-xs text-slate-400">Paste the JSON output generated from your mobile notepad photo</p>
        </div>
        <button onclick="closeIngestModal()" class="text-slate-400 hover:text-white text-xl font-bold">&times;</button>
      </div>

      <div>
        <div class="flex justify-between items-center mb-1">
          <label class="text-xs font-semibold text-slate-300">JSON Payload</label>
          <button onclick="loadSamplePayload()" class="text-xs text-indigo-400 hover:underline font-semibold">Load Sample Notepad JSON</button>
        </div>
        <textarea id="jsonInput" rows="10" class="w-full bg-slate-950 font-mono text-xs p-3 border border-slate-800 rounded-xl text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder='{"date": "2026-10-07", "transactions": [...]}'></textarea>
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
        document.getElementById('kpi-projected-rev').innerText = '₹' + forecast.total_projected_revenue.toLocaleString('en-IN');
        document.getElementById('kpi-target-month').innerText = forecast.target_month + ' Forecast';
        document.getElementById('forecast-header-sub').innerText = `Projected for ${forecast.target_month} (${forecast.target_season} Season) across ${forecast.forecast_items.length} key items.`;
        document.getElementById('forecast-season-badge').innerText = `Upcoming Season: ${forecast.target_season}`;

        const tbody = document.getElementById('forecast-table-body');
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

      // 2. Basket Co-Purchases
      const basketData = await fetchAPI('/api/basket-patterns');
      if (basketData && basketData.length > 0) {
        document.getElementById('kpi-top-pair').innerText = `${basketData[0].item_a} + ${basketData[0].item_b}`;
        document.getElementById('kpi-pair-stat').innerText = `${basketData[0].confidence_pct}% Co-Purchase Rate`;

        const container = document.getElementById('basket-pair-list');
        container.innerHTML = basketData.map(b => `
          <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800 hover:border-indigo-500/40 transition-colors">
            <div class="flex justify-between items-start gap-2">
              <div class="font-bold text-slate-200 text-xs flex items-center gap-1.5">
                <span class="text-indigo-400">${b.item_a}</span>
                <span class="text-slate-500">+</span>
                <span class="text-indigo-400">${b.item_b}</span>
              </div>
              <span class="bg-indigo-500/20 text-indigo-300 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-500/30">
                ${b.confidence_pct}% Rate (${b.times_bought_together} bills)
              </span>
            </div>
            <p class="text-[11px] text-slate-400 mt-1">${b.insight}</p>
          </div>
        `).join('');
      }

      // 3. Day of Week Patterns
      const dayData = await fetchAPI('/api/day-patterns');
      if (dayData) {
        const dContainer = document.getElementById('day-pattern-list');
        dContainer.innerHTML = dayData.map(d => `
          <div class="p-2.5 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
            <div>
              <span class="font-bold text-white text-xs">${d.day}</span>
              <p class="text-[11px] text-slate-400">${d.pattern_theme}</p>
              <p class="text-[10px] text-indigo-300 mt-0.5">Top Sellers: ${d.top_drivers.join(', ')}</p>
            </div>
            <div class="text-right">
              <span class="font-bold text-slate-200">₹${d.avg_basket_value}</span>
              <p class="text-[10px] text-slate-500">avg basket</p>
            </div>
          </div>
        `).join('');
      }

      // 4. Changing Trends (Surging vs Declining)
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

      // 5. Monthly Timeline Chart
      const monthlyHistory = await fetchAPI('/api/monthly-history');
      if (monthlyHistory) {
        renderMonthlyChart(monthlyHistory);
      }

      // 6. Festival Roadmap
      const roadmapData = await fetchAPI('/api/festival-roadmap');
      if (roadmapData && roadmapData.roadmap.length > 0) {
        const nextFest = roadmapData.roadmap[0];
        document.getElementById('kpi-next-fest').innerText = nextFest.name;
        document.getElementById('kpi-fest-days').innerText = `${nextFest.days_until} Days Remaining (${nextFest.target_date})`;

        const fContainer = document.getElementById('festivals-container');
        fContainer.innerHTML = roadmapData.roadmap.map(f => `
          <div class="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 flex flex-col justify-between">
            <div>
              <div class="flex justify-between items-start gap-2 mb-2">
                <h3 class="font-bold text-white text-xs">${f.name}</h3>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${f.days_until <= 30 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-slate-800 text-slate-300'}">
                  ${f.days_until} days
                </span>
              </div>
              <p class="text-[11px] text-slate-400 mb-2">📅 ${f.target_date} • ${f.status}</p>
              <div class="space-y-1.5 pt-2 border-t border-slate-800">
                ${f.key_items.map(k => `
                  <div class="text-[11px] text-slate-300 flex justify-between">
                    <span>${k.item}</span>
                    <span class="font-bold ${k.surge_pct > 0 ? 'text-amber-400' : 'text-slate-500'}">${k.surge_pct > 0 ? '+' : ''}${k.surge_pct}%</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        `).join('');
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
        "transactions": [
          {"raw_text": "2 amul taaza 500", "standardized_name": "Amul Taaza Milk 500ml", "category": "Dairy", "quantity": 2, "unit": "packet", "unit_price": 27.0, "total_amount": 54.0},
          {"raw_text": "1 marie gold", "standardized_name": "Britannia Marie Gold 120g", "category": "Snacks", "quantity": 1, "unit": "packet", "unit_price": 15.0, "total_amount": 15.0},
          {"raw_text": "3 maggi packet", "standardized_name": "Maggi 2-Minute Noodles 70g", "category": "Snacks", "quantity": 3, "unit": "packet", "unit_price": 14.0, "total_amount": 42.0},
          {"raw_text": "2 thumsup 250ml", "standardized_name": "Thums Up 250ml Bottle", "category": "Beverages", "quantity": 2, "unit": "bottle", "unit_price": 20.0, "total_amount": 40.0},
          {"raw_text": "cheeni 2kg 90", "standardized_name": "Sugar (Loose)", "category": "Staples", "quantity": 2, "unit": "kg", "unit_price": 45.0, "total_amount": 90.0}
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
          statusEl.innerText = `Ingested ${data.data.items_processed} items! Refreshing patterns & forecasts...`;
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

    window.addEventListener('DOMContentLoaded', loadAll);
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
