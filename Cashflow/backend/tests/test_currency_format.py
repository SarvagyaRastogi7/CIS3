from app.services.currency_format import format_context_for_llm, format_inr, format_inr_compact, normalize_inr_in_narrative


def test_format_inr():
    assert format_inr(668121) == "₹668,121"
    assert format_inr_compact(14447359) == "₹1.44 Cr"


def test_format_context_for_llm_converts_money_fields():
    context = {
        "forecast_summary": {"net_cash_flow": 14447359.59, "avg_monthly_cash_flow": 749930.17},
        "monthly_projection": [{"month": "2026-08-01", "total_sales": 1170650.86, "cash_flow": 668121.37}],
    }
    formatted = format_context_for_llm(context)
    assert formatted["forecast_summary"]["net_cash_flow"] == "₹1.44 Cr"
    assert "₹" in formatted["monthly_projection"][0]["total_sales"]


def test_normalize_inr_in_narrative_replaces_dollars():
    text = "Revenue grows from $1,170,650 to $14 million."
    cleaned = normalize_inr_in_narrative(text)
    assert "$" not in cleaned
    assert "₹" in cleaned
