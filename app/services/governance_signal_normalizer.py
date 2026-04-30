"""Signal normalization for governance metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NormalizedSignal:
    name: str
    raw: float
    min_value: float
    max_value: float
    normalized: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "raw": round(self.raw, 4),
            "min_value": round(self.min_value, 4),
            "max_value": round(self.max_value, 4),
            "normalized": round(self.normalized, 4),
        }


class GovernanceSignalNormalizerService:
    """Normalize heterogeneous governance metrics into 0..1 range."""

    def normalize(self, values: list[dict]) -> list[NormalizedSignal]:
        result: list[NormalizedSignal] = []
        for item in values:
            name = str(item.get("name") or "unknown")
            raw = float(item.get("raw") or 0.0)
            min_value = float(item.get("min") or 0.0)
            max_value = float(item.get("max") or 1.0)
            if max_value <= min_value:
                max_value = min_value + 1.0
            normalized = (raw - min_value) / (max_value - min_value)
            if normalized < 0:
                normalized = 0.0
            if normalized > 1:
                normalized = 1.0
            result.append(
                NormalizedSignal(
                    name=name,
                    raw=raw,
                    min_value=min_value,
                    max_value=max_value,
                    normalized=normalized,
                )
            )
        return result

    def summarize(self, values: list[dict]) -> dict:
        normalized = self.normalize(values)
        if not normalized:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "signals": []}
        arr = [item.normalized for item in normalized]
        return {
            "count": len(normalized),
            "avg": round(sum(arr) / len(arr), 4),
            "min": round(min(arr), 4),
            "max": round(max(arr), 4),
            "signals": [item.to_dict() for item in normalized],
        }
