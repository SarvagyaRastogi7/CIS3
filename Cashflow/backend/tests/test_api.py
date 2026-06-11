from datetime import date
from io import BytesIO
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.data_store import data_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    data_store.clear()
    yield
    data_store.clear()


def _excel_bytes(rows: int = 15) -> bytes:
    data = []
    for i in range(rows):
        sales = 100_000 + i * 5_000
        credit = sales * 0.6
        cash = sales - credit
        expenses = sales * 0.8
        cash_exp = expenses * 0.5
        credit_exp = expenses - cash_exp
        data.append(
            {
                "Month": date(2023 + (i // 12), (i % 12) + 1, 1).strftime("%b-%y"),
                "Total Sales": sales,
                "Total Credit Sales": credit,
                "Total Cash Sales": cash,
                "Collections": credit * 0.7,
                "Total Expenses": expenses,
                "Total Cash Expenses": cash_exp,
                "Total Credit Expenses": credit_exp,
                "Cash Paid for Credit Expenses": credit_exp * 0.75,
            }
        )
    df = pd.DataFrame(data)
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_upload_and_forecast(client):
    res = client.post(
        "/api/v1/data/upload",
        files={"file": ("test.xlsx", _excel_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 200
    res = client.post("/api/v1/forecast/base")
    assert res.status_code == 200
    body = res.json()
    assert len(body["forecast"]) == 12


def test_prompt_cashflow_advisory(client):
    client.post(
        "/api/v1/data/upload",
        files={"file": ("test.xlsx", _excel_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    res = client.post("/api/v1/prompt", json={"prompt": "How can I increase my cashflow?"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "cashflow_advisory"
    assert "executive_summary" in body["advisory"]
    assert len(body["advisory"]["levers"]) >= 1
    assert len(body["advisory"]["priority_actions"]) >= 1


@patch("app.services.llm_service.chat")
@patch("app.services.llm_service.is_available", return_value=True)
def test_forecast_includes_trajectory_narrative(mock_available, mock_chat, client, monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from app.config import get_settings

    get_settings.cache_clear()
    mock_chat.return_value = {
        "narrative": "Revenue rises steadily while expenditure grows more slowly, widening net cashflow.",
        "model": "gpt-4o-mini",
        "available": True,
        "error": None,
    }
    client.post(
        "/api/v1/data/upload",
        files={"file": ("test.xlsx", _excel_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    res = client.post("/api/v1/forecast/base")
    assert res.status_code == 200
    body = res.json()
    assert body["llm_narrative"]
    assert body["llm_available"] is True
    get_settings.cache_clear()


def test_upload_rejects_insufficient_data(client):
    res = client.post(
        "/api/v1/data/upload",
        files={"file": ("test.xlsx", _excel_bytes(6), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 422
