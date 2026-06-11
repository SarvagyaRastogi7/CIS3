from datetime import date, datetime

import pandas as pd
import pytest

from app.utils.dates import parse_month_value, parse_month_value_optional


def test_parse_month_value_accepts_date_and_strings():
    assert parse_month_value(date(2026, 5, 15)) == date(2026, 5, 1)
    assert parse_month_value("2026-05-01") == date(2026, 5, 1)
    assert parse_month_value("May-26") == date(2026, 5, 1)
    assert parse_month_value("2026-05") == date(2026, 5, 1)


def test_parse_month_value_accepts_datetime_and_timestamp():
    assert parse_month_value(datetime(2026, 5, 10, 12, 0)) == date(2026, 5, 1)
    assert parse_month_value(pd.Timestamp("2026-05-10")) == date(2026, 5, 1)


def test_parse_month_value_optional():
    assert parse_month_value_optional(None) is None
    assert parse_month_value_optional("Jan-24") == date(2024, 1, 1)


def test_parse_month_value_rejects_invalid():
    with pytest.raises(ValueError, match="Unable to parse month value"):
        parse_month_value("not-a-month")
