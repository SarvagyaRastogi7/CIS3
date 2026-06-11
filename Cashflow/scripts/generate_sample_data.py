"""Generate sample historical data matching the Foundry dataset pattern."""

from datetime import date
from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parents[1] / "sample_data" / "sample_data_foundry.xlsx"

# Anchor points from the reference dataset (month index 0 = Jan-23)
ANCHORS = {
    0: [100_000, 60_000, 40_000, 50_000, 80_000, 40_000, 40_000, 30_000],
    1: [120_000, 70_000, 50_000, 60_000, 90_000, 45_000, 45_000, 35_000],
    2: [150_000, 80_000, 70_000, 70_000, 100_000, 50_000, 50_000, 40_000],
    12: [400_000, 180_000, 220_000, 170_000, 200_000, 100_000, 100_000, 90_000],
    24: [700_000, 300_000, 400_000, 290_000, 320_000, 160_000, 160_000, 150_000],
    29: [850_000, 360_000, 490_000, 350_000, 380_000, 190_000, 190_000, 180_000],
    30: [850_000, 360_000, 490_000, 350_000, 380_000, 190_000, 190_000, 180_000],
}

COLUMNS = [
    "Total Sales",
    "Total Credit Sales",
    "Total Cash Sales",
    "Collections",
    "Total Expenses",
    "Total Cash Expenses",
    "Total Credit Expenses",
    "Cash Paid for Credit Expenses",
]


def _interpolate_values() -> list[list[int]]:
    sorted_idx = sorted(ANCHORS.keys())
    data = [[0] * 8 for _ in range(31)]

    for col_i in range(8):
        for seg in range(len(sorted_idx) - 1):
            start_i, end_i = sorted_idx[seg], sorted_idx[seg + 1]
            start_v, end_v = ANCHORS[start_i][col_i], ANCHORS[end_i][col_i]
            span = end_i - start_i
            for month in range(start_i, end_i + 1):
                t = (month - start_i) / span if span else 0
                value = round(start_v + t * (end_v - start_v))
                step = 5_000 if col_i < 4 else 10_000
                data[month][col_i] = round(value / step) * step

    for month in range(31):
        data[month][2] = data[month][0] - data[month][1]
        data[month][6] = data[month][4] - data[month][5]

    return data


def generate() -> None:
    values = _interpolate_values()
    start = date(2023, 1, 1)
    rows = []
    for i in range(31):
        month = pd.Timestamp(start) + pd.DateOffset(months=i)
        row = {"Month": month.strftime("%b-%y")}
        for j, col in enumerate(COLUMNS):
            row[col] = values[i][j]
        rows.append(row)

    df = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT, index=False, engine="openpyxl")
    print(f"Wrote {OUTPUT} ({len(df)} rows)")


if __name__ == "__main__":
    generate()
