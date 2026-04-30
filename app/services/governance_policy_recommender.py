"""Recommend policy tuning based on governance profile."""

from __future__ import annotations


class GovernancePolicyRecommenderService:
    def recommend(self, payload: dict) -> dict:
        score = float(payload.get("score") or 0.0)
        volatility = float(payload.get("volatility") or 0.0)
        incidents = int(payload.get("incidents") or 0)

        mode = "hold"
        adjustments: dict[str, float] = {
            "quality_floor_delta": 0.0,
            "evidence_min_delta": 0.0,
            "sampling_rate_delta": 0.0,
        }

        if score < 60 or incidents > 0:
            mode = "tighten"
            adjustments["quality_floor_delta"] = 5.0
            adjustments["evidence_min_delta"] = 10.0
            adjustments["sampling_rate_delta"] = 0.2
        elif score > 85 and volatility < 0.1 and incidents == 0:
            mode = "relax"
            adjustments["quality_floor_delta"] = -2.0
            adjustments["evidence_min_delta"] = -5.0
            adjustments["sampling_rate_delta"] = -0.1

        return {
            "mode": mode,
            "adjustments": adjustments,
            "inputs": {
                "score": score,
                "volatility": volatility,
                "incidents": incidents,
            },
        }
