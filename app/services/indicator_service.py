# 用途：负责通用技术指标计算，供单股查询和选股服务复用。
from __future__ import annotations

from typing import Any


class IndicatorService:
    def calculate_simple_moving_average(
        self,
        rows: list[dict[str, Any]],
        window: int,
        price_field: str = "close",
    ) -> list[dict[str, Any]]:
        if window <= 0:
            raise ValueError("window must be greater than 0")

        ordered_rows = list(reversed(rows))
        values: list[float] = []
        result: list[dict[str, Any]] = []

        for row in ordered_rows:
            raw_value = row.get(price_field)
            if raw_value is None:
                values.append(0.0)
            else:
                values.append(float(raw_value))

            if len(values) < window:
                moving_average = None
            else:
                window_values = values[-window:]
                moving_average = round(sum(window_values) / window, 4)

            enriched_row = dict(row)
            enriched_row[f"ma_{window}"] = moving_average
            result.append(enriched_row)

        result.reverse()
        return result
