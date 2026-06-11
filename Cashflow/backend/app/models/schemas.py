from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.dates import parse_month_value, parse_month_value_optional


class ScenarioType(str, Enum):
    BASE = "base"
    CUSTOM_STRESS = "custom_stress"
    DELAYED_RECEIVABLES = "delayed_receivables"
    INCREASED_SUPPLIER_PAYOUT = "increased_supplier_payout"
    DELAYED_AND_SPENDING = "delayed_and_spending"


class ScenarioStressParams(BaseModel):
    """User-tunable stress assumptions applied on top of the ARIMA base forecast."""

    stress_receivables: bool = Field(default=True, description="Apply delayed / reduced collections")
    receivables_delay_months: int = Field(default=2, ge=0, le=6)
    receivables_collection_factor: float = Field(
        default=0.7,
        ge=0,
        le=1.5,
        description="Collections as a fraction of credit sales after lag",
    )
    stress_supplier_payout: bool = Field(default=True, description="Increase cash paid on credit expenses")
    supplier_payout_increase_pct: float = Field(default=0.2, ge=0, le=1.0)
    stress_expenses: bool = Field(default=False, description="Increase all expense lines")
    expense_increase_pct: float = Field(default=0.2, ge=0, le=1.0)


class MonthlyRecord(BaseModel):
    month: date
    total_sales: float = Field(gt=0)
    total_credit_sales: float = Field(ge=0)
    total_cash_sales: float = Field(ge=0)
    collections: float = Field(ge=0)
    total_expenses: float = Field(ge=0)
    total_cash_expenses: float = Field(ge=0)
    total_credit_expenses: float = Field(ge=0)
    cash_paid_credit_expenses: float = Field(ge=0)

    @field_validator("month", mode="before")
    @classmethod
    def parse_month(cls, v: Any) -> date:
        return parse_month_value(v)


class DerivedRatios(BaseModel):
    cash_sale_percent: float
    expense_ratio: float
    cash_expense_ratio: float
    credit_expenses_paid_ratio: float
    credit_sales_ratio: float
    avg_collection_lag_days: float
    avg_payment_lag_days: float


class CashflowRecord(MonthlyRecord):
    cash_flow: float
    cash_inflows: float
    cash_outflows: float


class ForecastAssumptions(BaseModel):
    forecast_start: Optional[date] = None
    forecast_end: Optional[date] = None

    @field_validator("forecast_start", "forecast_end", mode="before")
    @classmethod
    def normalize_forecast_month(cls, v: Any) -> Optional[date]:
        return parse_month_value_optional(v)

    @model_validator(mode="after")
    def validate_forecast_range(self) -> "ForecastAssumptions":
        if self.forecast_start and self.forecast_end:
            if self.forecast_end < self.forecast_start:
                raise ValueError("forecast_end must be on or after forecast_start.")
            span = (
                (self.forecast_end.year - self.forecast_start.year) * 12
                + (self.forecast_end.month - self.forecast_start.month)
                + 1
            )
            if span > 24:
                raise ValueError("Forecast range cannot exceed 24 months.")
        elif self.forecast_start or self.forecast_end:
            raise ValueError("Both forecast_start and forecast_end are required.")
        return self


class TrendForecastRequest(BaseModel):
    months_ahead: int = Field(default=5, ge=1, le=24)


class ScenarioRequest(BaseModel):
    assumptions: Optional[ForecastAssumptions] = None
    stress_params: ScenarioStressParams = Field(default_factory=ScenarioStressParams)
    scenarios: List[ScenarioType] = Field(
        default_factory=lambda: [
            ScenarioType.BASE,
            ScenarioType.CUSTOM_STRESS,
        ]
    )


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)


class ValidationIssue(BaseModel):
    severity: str
    field: str
    message: str


class ValidationReport(BaseModel):
    valid: bool
    issues: List[ValidationIssue]
    record_count: int


class ForecastMonth(BaseModel):
    month: date
    total_sales: float
    total_credit_sales: float
    total_cash_sales: float
    collections: float
    total_expenses: float
    total_cash_expenses: float
    total_credit_expenses: float
    cash_paid_credit_expenses: float
    cash_flow: float
    model_mom_change_pct: Optional[float] = None


class ForecastResponse(BaseModel):
    assumptions: ForecastAssumptions
    derived_ratios: DerivedRatios
    validation: ValidationReport
    forecast: List[ForecastMonth]
    summary: Dict[str, float]
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    llm_narrative: Optional[str] = None
    llm_model: Optional[str] = None
    llm_available: Optional[bool] = None
    llm_error: Optional[str] = None


class ScenarioForecast(BaseModel):
    scenario: ScenarioType
    label: str
    forecast: List[ForecastMonth]
    summary: Dict[str, float]


class ScenarioResponse(BaseModel):
    base_assumptions: ForecastAssumptions
    stress_params: ScenarioStressParams
    scenarios: List[ScenarioForecast]


class InsightItem(BaseModel):
    category: str
    title: str
    description: str
    impact: str
    source: Optional[str] = None


class InsightsResponse(BaseModel):
    seasonal_patterns: List[Dict[str, Any]]
    llm_insights: List[InsightItem] = Field(default_factory=list)
    historical_summary: Dict[str, Any]
    llm_narrative: Optional[str] = None
    llm_model: Optional[str] = None
    llm_available: bool = False
    llm_error: Optional[str] = None


class LlmStatusResponse(BaseModel):
    enabled: bool
    provider: str = "openai"
    base_url: str
    configured_model: str
    resolved_model: Optional[str] = None
    models: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
