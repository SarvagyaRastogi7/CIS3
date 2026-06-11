from datetime import date

from app.guardrails.validators import validate_records
from tests.factories import make_monthly_record, make_monthly_records


def test_validate_records_requires_minimum_months():
    records = [make_monthly_record(date(2023, month, 1)) for month in range(1, 7)]
    report = validate_records(records)
    assert not report.valid
    assert any(i.field == "record_count" for i in report.issues)


def test_validate_records_passes_with_sufficient_data():
    records = make_monthly_records(15, sales_step=1_000)
    report = validate_records(records)
    assert report.valid


def test_validate_records_flags_inconsistent_sales():
    records = make_monthly_records(15)
    bad = records[5].model_copy(update={"total_cash_sales": 1, "total_credit_sales": 1})
    records[5] = bad
    report = validate_records(records)
    assert report.valid
    assert any(i.field == "total_sales" for i in report.issues)
