from analytics import (
    get_day_of_week_patterns,
    get_changing_trend_patterns,
    get_basket_co_purchases,
    get_weather_impact_analysis,
    get_time_of_day_patterns
)

def test_day_of_week_patterns_structure():
    days = get_day_of_week_patterns()
    assert isinstance(days, list)
    assert len(days) == 7
    for d in days:
        assert "day" in d
        assert "total_baskets" in d
        assert "total_revenue" in d
        assert "avg_basket_value" in d
        assert "pattern_theme" in d

def test_changing_trend_patterns_momentum_guard():
    trends = get_changing_trend_patterns()
    assert "surging_products" in trends
    assert "declining_products" in trends
    assert "all_product_trends" in trends
    for item in trends["all_product_trends"]:
        assert "growth_pct" in item
        assert "momentum_status" in item
        # Ensure growth_pct is never None or NaN
        assert isinstance(item["growth_pct"], (int, float))

def test_basket_co_purchases_contract():
    baskets = get_basket_co_purchases(min_pairs=2)
    if isinstance(baskets, dict) and baskets.get("is_gated"):
        assert baskets["status"] == "sample_gating"
        assert baskets["threshold_bills"] == 25
    elif isinstance(baskets, list):
        for pair in baskets:
            assert "item_a" in pair
            assert "item_b" in pair
            assert "confidence_pct" in pair
            assert "lift" in pair

def test_weather_impact_analysis_returns_list():
    weather_data = get_weather_impact_analysis()
    assert isinstance(weather_data, list)

def test_time_of_day_patterns_returns_list():
    time_data = get_time_of_day_patterns()
    assert isinstance(time_data, list)
