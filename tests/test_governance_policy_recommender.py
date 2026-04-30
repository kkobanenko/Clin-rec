"""Tests for governance policy recommender."""

from __future__ import annotations

from app.services.governance_policy_recommender import GovernancePolicyRecommenderService


def test_recommender_tighten():
    svc = GovernancePolicyRecommenderService()
    rep = svc.recommend({"score": 50, "volatility": 0.3, "incidents": 1})
    assert rep["mode"] == "tighten"


def test_recommender_relax():
    svc = GovernancePolicyRecommenderService()
    rep = svc.recommend({"score": 92, "volatility": 0.05, "incidents": 0})
    assert rep["mode"] == "relax"
