from app.models.schemas import ForecastAssumptions, ScenarioStressParams, ScenarioType
from app.services.forecast_engine import format_stress_label, generate_scenario_forecasts
from tests.factories import make_monthly_records


def test_custom_stress_responds_to_params():
    records = make_monthly_records()
    mild = ScenarioStressParams(
        stress_receivables=True,
        receivables_delay_months=1,
        receivables_collection_factor=0.9,
        stress_supplier_payout=False,
        stress_expenses=False,
    )
    severe = ScenarioStressParams(
        stress_receivables=True,
        receivables_delay_months=3,
        receivables_collection_factor=0.5,
        stress_supplier_payout=True,
        supplier_payout_increase_pct=0.3,
        stress_expenses=True,
        expense_increase_pct=0.25,
    )

    _, _, _, mild_dfs, _ = generate_scenario_forecasts(
        records,
        ForecastAssumptions(),
        [ScenarioType.BASE, ScenarioType.CUSTOM_STRESS],
        mild,
    )
    _, _, _, severe_dfs, _ = generate_scenario_forecasts(
        records,
        ForecastAssumptions(),
        [ScenarioType.BASE, ScenarioType.CUSTOM_STRESS],
        severe,
    )

    mild_cf = float(mild_dfs[ScenarioType.CUSTOM_STRESS]["cash_flow"].sum())
    severe_cf = float(severe_dfs[ScenarioType.CUSTOM_STRESS]["cash_flow"].sum())
    base_cf = float(mild_dfs[ScenarioType.BASE]["cash_flow"].sum())

    assert mild_cf != base_cf
    assert severe_cf < mild_cf


def test_format_stress_label_includes_toggles():
    label = format_stress_label(
        ScenarioStressParams(
            stress_receivables=True,
            receivables_delay_months=2,
            receivables_collection_factor=0.7,
            stress_supplier_payout=True,
            supplier_payout_increase_pct=0.2,
            stress_expenses=False,
        )
    )
    assert "2mo delay" in label
    assert "70% collections" in label
    assert "+20% supplier payout" in label
