import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from logging_config import get_logger
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
from schemas import SalesIngestPayload

logger = get_logger("main")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
INDEX_HTML_PATH = os.path.join(TEMPLATES_DIR, "index.html")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager replacing deprecated @app.on_event."""
    logger.info("Initializing Kirana Demand & Predictive Forecasting System...")
    init_db()
    if settings.allow_synthetic_seed:
        logger.info("ALLOW_SYNTHETIC_SEED=true: Initializing synthetic transactions.")
        seed_database()
    else:
        logger.info("Production Mode Active: Operating exclusively on real store records.")
    yield
    logger.info("Shutting down Kirana Retail Intelligence System.")

app = FastAPI(
    title="Kirana Demand Pattern & Predictive Forecasting",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Analytics & Forecasting Endpoints ---

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
        logger.error(f"Error fetching AI insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-insights/refresh")
def api_ai_insights_refresh():
    try:
        return enrich_analytics_with_gemini(force_refresh=True)
    except Exception as e:
        logger.error(f"Error refreshing AI insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/festival-trend/crawl")
def api_crawl_festival_trend(festival: str, year: Optional[int] = None):
    try:
        from festival_trend_crawler import crawl_and_update_festival_trend
        target_year = year or datetime.now().year
        res = crawl_and_update_festival_trend(festival, target_year, force=True)
        return {"status": "success", "data": res}
    except Exception as e:
        logger.error(f"Error crawling trend for '{festival}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
def api_ingest(payload: SalesIngestPayload):
    try:
        result = ingest_gemini_sales_json(payload.model_dump())
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Failed to ingest sales batch: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reset-data")
def api_reset():
    seed_database()
    return {"status": "success", "message": "Historical data re-initialized."}

# --- Dashboard UI Presentation ---

@app.get("/", response_class=HTMLResponse)
def index_page():
    if not os.path.exists(INDEX_HTML_PATH):
        raise HTTPException(status_code=404, detail="Dashboard template not found.")
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
