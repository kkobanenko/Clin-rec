# DISCOVERY COMPLETENESS PLAN v1

Дата: 2026-04-25

Этот документ — canonical discovery completeness plan в `docs/`.
Основной source content: [../DISCOVERY_COMPLETENESS_PLAN_v1.md](../DISCOVERY_COMPLETENESS_PLAN_v1.md).

## Problem

Smoke discovery и completeness claim сейчас могут смешиваться в операторском восприятии.

## Target

Явно разделить:

- runtime lifecycle validation (smoke),
- corpus completeness signal (corpus mode).

## Required reporting

Добавить structured `discovery_strategy_report` со strategy/fallback/counts/limit/completeness fields в `stats_json`.

## Acceptance

- Smoke output не трактуется как proof of corpus completeness.
- Operator видит fallback reason и completeness mode.
