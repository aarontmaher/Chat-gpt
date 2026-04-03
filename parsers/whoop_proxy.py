from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import requests

from config import WHOOP_TOKENS_FILE


WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


def get_normalized_daily(date: str, tokens_path: str = WHOOP_TOKENS_FILE) -> dict[str, Any]:
    """Return a normalized WHOOP daily object for the requested ISO date."""
    normalized_date = normalize_date(date)
    if not normalized_date:
        return {"error": "WHOOP auth failed"}

    tokens = load_whoop_tokens(tokens_path)
    if not tokens:
        return {"error": "WHOOP auth failed"}

    access_token = tokens.get("access_token")
    if not access_token:
        refreshed = refresh_whoop_tokens(tokens, tokens_path=tokens_path)
        access_token = refreshed.get("access_token") if refreshed else None
    if not access_token:
        return {"error": "WHOOP auth failed"}

    try:
        recovery = fetch_paginated("/recovery", access_token)
        cycle = fetch_paginated("/cycle", access_token)
        sleep = fetch_paginated("/activity/sleep", access_token)
        workouts = fetch_paginated("/activity/workout", access_token)
    except requests.RequestException:
        refreshed = refresh_whoop_tokens(tokens, tokens_path=tokens_path)
        access_token = refreshed.get("access_token") if refreshed else None
        if not access_token:
            return {"error": "WHOOP auth failed"}
        try:
            recovery = fetch_paginated("/recovery", access_token)
            cycle = fetch_paginated("/cycle", access_token)
            sleep = fetch_paginated("/activity/sleep", access_token)
            workouts = fetch_paginated("/activity/workout", access_token)
        except requests.RequestException:
            return {"error": "WHOOP auth failed"}

    return {
        "date": normalized_date,
        "recovery": normalize_recovery(find_record_for_date(recovery, normalized_date)),
        "strain": normalize_cycle(find_record_for_date(cycle, normalized_date)),
        "sleep": normalize_sleep(find_record_for_date(sleep, normalized_date)),
        "workouts": [normalize_workout(item) for item in find_records_for_date(workouts, normalized_date)],
    }


def load_whoop_tokens(tokens_path: str = WHOOP_TOKENS_FILE) -> dict[str, Any]:
    try:
        with open(tokens_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def refresh_whoop_tokens(tokens: dict[str, Any], tokens_path: str = WHOOP_TOKENS_FILE) -> dict[str, Any]:
    refresh_token = tokens.get("refresh_token")
    client_id = os.getenv("WHOOP_CLIENT_ID")
    client_secret = os.getenv("WHOOP_CLIENT_SECRET")
    if not refresh_token or not client_id or not client_secret:
        return {}

    response = requests.post(
        WHOOP_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    if response.status_code >= 400:
        return {}

    payload = response.json()
    if not isinstance(payload, dict) or not payload.get("access_token"):
        return {}

    merged = dict(tokens)
    merged.update(payload)
    try:
        os.makedirs(os.path.dirname(tokens_path), exist_ok=True)
        with open(tokens_path, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2)
    except OSError:
        return payload
    return merged


def fetch_paginated(endpoint: str, access_token: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    next_token: str | None = None

    while True:
        params: dict[str, Any] = {}
        if next_token:
            params["nextToken"] = next_token

        response = requests.get(
            f"{WHOOP_API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        page_items = payload.get("records") or payload.get("items") or []
        if isinstance(page_items, list):
            records.extend(item for item in page_items if isinstance(item, dict))

        next_token = payload.get("nextToken") or payload.get("next_token") or payload.get("cursor")
        if not next_token:
            break

    return records


def normalize_date(value: str) -> str:
    if not value:
        return ""
    raw = value.strip()
    if len(raw) == 10:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
        except ValueError:
            return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return ""


def find_record_for_date(records: list[dict[str, Any]], target_date: str) -> dict[str, Any]:
    for item in records:
        if record_date(item) == target_date:
            return item
    return {}


def find_records_for_date(records: list[dict[str, Any]], target_date: str) -> list[dict[str, Any]]:
    return [item for item in records if record_date(item) == target_date]


def record_date(item: dict[str, Any]) -> str:
    for key in (
        "date",
        "start",
        "start_time",
        "created_at",
        "updated_at",
        "end",
        "end_time",
    ):
        value = item.get(key)
        normalized = normalize_date(str(value)) if value else ""
        if normalized:
            return normalized
    score = item.get("score") or {}
    for key in ("date", "updated_at"):
        value = score.get(key)
        normalized = normalize_date(str(value)) if value else ""
        if normalized:
            return normalized
    return ""


def normalize_recovery(item: dict[str, Any]) -> dict[str, Any]:
    score = item.get("score") or {}
    return {
        "score": first_number((item, score), "recovery_score", "score"),
        "hrv_ms": first_number((item, score), "hrv_rmssd_milli", "hrv_ms", "hrv"),
        "rhr_bpm": first_number((item, score), "resting_heart_rate", "rhr_bpm"),
        "spo2_pct": first_number((item, score), "spo2_percentage", "spo2_pct"),
        "skin_temp_c": first_number((item, score), "skin_temp_celsius", "skin_temp_c"),
    }


def normalize_cycle(item: dict[str, Any]) -> dict[str, Any]:
    score = item.get("score") or {}
    return {
        "day_strain": first_number((item, score), "strain", "day_strain"),
        "kilojoules": first_number((item, score), "kilojoules"),
        "avg_hr": first_number((item, score), "average_heart_rate", "avg_hr"),
        "max_hr": first_number((item, score), "max_heart_rate", "max_hr"),
    }


def normalize_sleep(item: dict[str, Any]) -> dict[str, Any]:
    score = item.get("score") or {}
    return {
        "performance_pct": first_number((item, score), "sleep_performance_percentage", "performance_pct"),
        "efficiency_pct": first_number((item, score), "sleep_efficiency_percentage", "efficiency_pct"),
        "total_hours": seconds_to_hours(first_number((item, score), "total_in_bed_time_milli", "total_sleep_time_milli")),
        "sws_hours": seconds_to_hours(first_number((item, score), "slow_wave_sleep_time_milli", "sws_time_milli")),
        "rem_hours": seconds_to_hours(first_number((item, score), "rem_sleep_time_milli", "rem_time_milli")),
        "needed_hours": seconds_to_hours(first_number((item, score), "sleep_needed_milli", "needed_sleep_milli")),
        "debt_hours": seconds_to_hours(first_number((item, score), "sleep_debt_milli", "debt_sleep_milli")),
        "respiratory_rate": first_number((item, score), "respiratory_rate"),
    }


def normalize_workout(item: dict[str, Any]) -> dict[str, Any]:
    score = item.get("score") or {}
    return {
        "sport_id": item.get("sport_id"),
        "strain": first_number((item, score), "strain"),
        "duration_min": minutes_from_seconds(first_number((item,), "duration_milli", "duration_ms", "duration")),
        "avg_hr": first_number((item, score), "average_heart_rate", "avg_hr"),
        "max_hr": first_number((item, score), "max_heart_rate", "max_hr"),
    }


def first_number(containers: tuple[Any, ...], *keys: str) -> float | int | None:
    flat_containers: list[Any] = list(containers)
    key_list = list(keys)
    for container in flat_containers:
        if not isinstance(container, dict):
            continue
        for key in key_list:
            value = container.get(key)
            if isinstance(value, (int, float)):
                return value
    return None


def seconds_to_hours(value: float | int | None) -> float | None:
    if value is None:
        return None
    # WHOOP often returns milliseconds.
    divisor = 3600000 if value > 10000 else 3600
    return round(float(value) / divisor, 2)


def minutes_from_seconds(value: float | int | None) -> int | None:
    if value is None:
        return None
    divisor = 60000 if value > 10000 else 60
    return int(round(float(value) / divisor))
