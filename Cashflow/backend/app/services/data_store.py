from __future__ import annotations

import threading
from typing import List, Optional

from app.models.schemas import MonthlyRecord


class DataStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: List[MonthlyRecord] = []
        self._source_filename: Optional[str] = None

    def set_records(self, records: List[MonthlyRecord], filename: Optional[str] = None) -> None:
        with self._lock:
            self._records = records
            self._source_filename = filename

    def get_records(self) -> List[MonthlyRecord]:
        with self._lock:
            return list(self._records)

    def get_filename(self) -> Optional[str]:
        with self._lock:
            return self._source_filename

    def has_data(self) -> bool:
        with self._lock:
            return len(self._records) > 0

    def clear(self) -> None:
        with self._lock:
            self._records = []
            self._source_filename = None


data_store = DataStore()
