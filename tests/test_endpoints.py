def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Kirana Demand & Pattern Forecasting" in response.text

def test_festival_roadmap_endpoint(client):
    response = client.get("/api/festival-roadmap")
    assert response.status_code == 200
    data = response.json()
    assert "roadmap" in data
    assert isinstance(data["roadmap"], list)
    assert len(data["roadmap"]) > 0

def test_basket_patterns_endpoint(client):
    response = client.get("/api/basket-patterns")
    assert response.status_code == 200
    data = response.json()
    # Either list of pairs or sample_gating dict
    assert isinstance(data, (list, dict))

def test_day_patterns_endpoint(client):
    response = client.get("/api/day-patterns")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

def test_time_patterns_endpoint(client):
    response = client.get("/api/time-patterns")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_weather_patterns_endpoint(client):
    response = client.get("/api/weather-patterns")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_changing_trends_endpoint(client):
    response = client.get("/api/changing-trends")
    assert response.status_code == 200
    data = response.json()
    assert "surging_products" in data
    assert "declining_products" in data

def test_monthly_history_endpoint(client):
    response = client.get("/api/monthly-history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_next_month_forecast_endpoint(client):
    response = client.get("/api/next-month-forecast")
    assert response.status_code == 200
    data = response.json()
    assert "target_month" in data
    assert "forecast_items" in data

def test_ai_insights_endpoint(client):
    response = client.get("/api/ai-insights")
    assert response.status_code == 200
    data = response.json()
    assert "daily_executive_summary" in data
