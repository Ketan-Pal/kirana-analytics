from forecasting import get_next_month_forecast, get_seasonal_and_festival_roadmap

def test_next_month_forecast_structure():
    forecast = get_next_month_forecast()
    assert "target_month" in forecast
    assert "target_season" in forecast
    assert "total_projected_revenue" in forecast
    assert "total_projected_units" in forecast
    assert "forecast_items" in forecast
    assert isinstance(forecast["forecast_items"], list)

    for item in forecast["forecast_items"]:
        assert "name" in item
        assert "category" in item
        assert "projected_next_month_qty" in item
        assert "stocking_action" in item

def test_seasonal_and_festival_roadmap_structure():
    roadmap = get_seasonal_and_festival_roadmap()
    assert "current_date" in roadmap
    assert "roadmap" in roadmap
    assert isinstance(roadmap["roadmap"], list)
    assert len(roadmap["roadmap"]) > 0

    for fest in roadmap["roadmap"]:
        assert "name" in fest
        assert "target_date" in fest
        assert "days_until" in fest
        assert "status" in fest
        assert "key_items" in fest
        assert "source" in fest
