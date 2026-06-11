from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.guardrails.validators import check_file_size, sanitize_upload_filename, validate_records
from app.models.schemas import (
    ForecastAssumptions,
    ForecastMonth,
    ForecastResponse,
    HealthResponse,
    InsightsResponse,
    LlmStatusResponse,
    MonthlyRecord,
    PromptRequest,
    ScenarioForecast,
    ScenarioRequest,
    ScenarioResponse,
    ScenarioStressParams,
    ScenarioType,
    TrendForecastRequest,
    ValidationReport,
)
from app.services.data_loader import load_from_excel
from app.services.data_store import data_store
from app.services.excel_export import export_forecast_to_excel, export_scenarios_to_excel
from app.services.forecast_engine import (
    generate_base_forecast,
    generate_scenario_forecasts,
    generate_trend_forecast,
    scenario_df_summary,
    scenario_label,
)
from app.services.openai_client import list_models, resolve_model
from app.services.llm_service import build_insights_response, generate_trajectory_narrative, llm_status
from app.services.prompt_router import route_prompt

router = APIRouter()


def _require_data() -> List[MonthlyRecord]:
    if not data_store.has_data():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data loaded. Upload an Excel file first.",
        )
    return data_store.get_records()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.post("/data/upload", response_model=ValidationReport)
async def upload_data(file: UploadFile = File(...)) -> ValidationReport:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are accepted.")

    content = await file.read()
    ok, message = check_file_size(len(content))
    if not ok:
        raise HTTPException(status_code=400, detail=message)

    try:
        records = load_from_excel(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    report = validate_records(records)
    if not report.valid:
        raise HTTPException(
            status_code=422,
            detail={"message": "Data validation failed.", "issues": [i.model_dump() for i in report.issues]},
        )

    filename = sanitize_upload_filename(file.filename)
    data_store.set_records(records, filename)
    return report


@router.get("/data/history")
async def get_history() -> dict:
    _require_data()
    records = data_store.get_records()
    return {
        "filename": data_store.get_filename(),
        "record_count": len(records),
        "records": [r.model_dump() for r in records],
    }


@router.post("/forecast/base", response_model=ForecastResponse)
async def base_forecast(assumptions: ForecastAssumptions | None = None) -> ForecastResponse:
    records = _require_data()
    assumptions = assumptions or ForecastAssumptions()
    forecast, ratios, summary, issues, model_info = generate_base_forecast(records, assumptions)
    validation = validate_records(records)
    validation.issues.extend(issues)
    response = ForecastResponse(
        assumptions=assumptions,
        derived_ratios=ratios,
        validation=validation,
        forecast=forecast,
        summary=summary,
        model_metadata=model_info,
    )
    if get_settings().llm_enabled:
        llm_payload = await asyncio.to_thread(
            generate_trajectory_narrative,
            records,
            forecast,
            summary,
        )
        return ForecastResponse(**{**response.model_dump(), **llm_payload})
    return response


@router.post("/forecast/trend")
async def trend_forecast(body: TrendForecastRequest) -> dict:
    records = _require_data()
    forecast, model_info = generate_trend_forecast(records, months_ahead=body.months_ahead)
    return {
        "months_ahead": body.months_ahead,
        "forecast": [f.model_dump() for f in forecast],
        "model_metadata": model_info,
    }


@router.post("/forecast/scenarios", response_model=ScenarioResponse)
async def scenario_forecast(body: ScenarioRequest | None = None) -> ScenarioResponse:
    records = _require_data()
    body = body or ScenarioRequest()
    _, _, assumptions, scenario_dfs, _ = generate_scenario_forecasts(
        records,
        body.assumptions,
        body.scenarios,
        body.stress_params,
    )

    scenarios: List[ScenarioForecast] = []
    for stype in body.scenarios:
        df = scenario_dfs[stype]
        scenarios.append(
            ScenarioForecast(
                scenario=stype,
                label=scenario_label(stype, body.stress_params),
                forecast=[ForecastMonth(**row) for row in df.to_dict(orient="records")],
                summary=scenario_df_summary(df),
            )
        )

    return ScenarioResponse(
        base_assumptions=assumptions or ForecastAssumptions(),
        stress_params=body.stress_params,
        scenarios=scenarios,
    )


@router.post("/prompt")
async def process_prompt(body: PromptRequest) -> dict:
    records = _require_data()
    return await asyncio.to_thread(route_prompt, records, body)


@router.get("/insights", response_model=InsightsResponse)
async def insights() -> InsightsResponse:
    records = _require_data()
    return await asyncio.to_thread(build_insights_response, records)


@router.get("/llm/status", response_model=LlmStatusResponse)
async def llm_status() -> LlmStatusResponse:
    status = await asyncio.to_thread(llm_status)
    return LlmStatusResponse(**status)


@router.get("/export/forecast")
async def export_forecast(forecast_start: str | None = None, forecast_end: str | None = None):
    records = _require_data()
    assumptions = ForecastAssumptions(
        forecast_start=forecast_start,
        forecast_end=forecast_end,
    )
    forecast, _, _, _, _ = generate_base_forecast(records, assumptions)
    label = f"{forecast_start}_{forecast_end}" if forecast_start and forecast_end else "default"
    content = export_forecast_to_excel(forecast, sheet_name=f"Forecast {label}")
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="cashflow_forecast_{label}.xlsx"'},
    )


@router.get("/export/scenarios")
async def export_scenarios(
    forecast_start: str | None = None,
    forecast_end: str | None = None,
    stress_receivables: bool = True,
    receivables_delay_months: int = 2,
    receivables_collection_factor: float = 0.7,
    stress_supplier_payout: bool = True,
    supplier_payout_increase_pct: float = 0.2,
    stress_expenses: bool = False,
    expense_increase_pct: float = 0.2,
):
    records = _require_data()
    assumptions = ForecastAssumptions(
        forecast_start=forecast_start,
        forecast_end=forecast_end,
    )
    stress_params = ScenarioStressParams(
        stress_receivables=stress_receivables,
        receivables_delay_months=receivables_delay_months,
        receivables_collection_factor=receivables_collection_factor,
        stress_supplier_payout=stress_supplier_payout,
        supplier_payout_increase_pct=supplier_payout_increase_pct,
        stress_expenses=stress_expenses,
        expense_increase_pct=expense_increase_pct,
    )
    _, _, _, scenario_dfs, _ = generate_scenario_forecasts(
        records,
        assumptions=assumptions,
        stress_params=stress_params,
    )
    payload = {
        scenario_label(k, stress_params): df.to_dict(orient="records") for k, df in scenario_dfs.items()
    }
    content = export_scenarios_to_excel(payload)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="cashflow_scenarios.xlsx"'},
    )
