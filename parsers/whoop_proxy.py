from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

import requests

from config import WHOOP_SQLITE_FILE, WHOOP_TOKENS_FILE


WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


RAILWAY_WHOOP_HEALTH_URL = "https://whoop-mcp-production-032e.up.railway.app/healthz"
RAILWAY_WHOOP_DIAG_URL = "https://whoop-mcp-production-032e.up.railway.app/diag/token-check"


def _get_from_railway_health(date: str) -> dict[str, Any] | None:
    """Try to get WHOOP daily info from the Railway production backend."""
    try:
        resp = requests.get(RAILWAY_WHOOP_HEALTH_URL, timeout=8)
        if resp.status_code != 200:
            return None
        health = resp.json()
        if not health.get("ok"):
            return None
        auth = health.get("auth") or {}
        latest_sync = health.get("latest_sync") or {}
        return {
            "date": health.get("latest_local_date") or date,
            "requested_date": date,
            "source": "railway_production",
            "latest_local_date": health.get("latest_local_date"),
            "recovery": None,  # Health endpoint doesn't return daily metrics
            "strain": None,
            "sleep": None,
            "workouts": None,
            "auth": {
                "state": "connected" if not auth.get("reauth_required") else "reauth_required",
                "token_source": auth.get("token_source"),
                "last_api_success_at": auth.get("last_api_success_at"),
                "sync_blocked": auth.get("sync_blocked_by_auth", False),
            },
            "freshness": {
                "state": "fresh" if health.get("latest_local_date") == date else "stale",
                "latest_date": health.get("latest_local_date"),
                "last_sync": latest_sync.get("finished_at"),
                "sync_source": latest_sync.get("source"),
            },
        }
    except Exception:
        return None


def get_normalized_daily(
    date: str,
    tokens_path: str = WHOOP_TOKENS_FILE,
    sqlite_path: str = WHOOP_SQLITE_FILE,
) -> dict[str, Any]:
    """Return a normalized WHOOP daily object for the requested ISO date.

    Priority: Railway production backend → local SQLite → local WHOOP API.
    """
    normalized_date = normalize_date(date)
    if not normalized_date:
        return {"error": "invalid_date"}

    # 1. Try Railway production backend (canonical source)
    railway_item = _get_from_railway_health(normalized_date)
    if railway_item is not None:
        return railway_item

    # 2. Fallback: local SQLite
    sqlite_item = get_normalized_daily_from_sqlite(normalized_date, sqlite_path=sqlite_path)
    if sqlite_item is not None:
        sqlite_item["source"] = "whoop_sqlite_local_fallback"
        return sqlite_item

    # 3. Fallback: local WHOOP API (stale tokens)
    live_item = get_normalized_daily_from_api(normalized_date, tokens_path=tokens_path)
    live_item.setdefault("requested_date", normalized_date)
    live_item.setdefault("source", "whoop_live_api_local_fallback")
    live_item.setdefault("freshness", {"state": "unknown"})
    live_item.setdefault("auth", {"state": "unknown"})
    return live_item


def get_normalized_daily_from_sqlite(date: str, sqlite_path: str = WHOOP_SQLITE_FILE) -> dict[str, Any] | None:
    if not os.path.exists(sqlite_path):
        return None

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT *
            FROM daily_summaries
            WHERE local_date = ?
            ORDER BY local_date DESC
            LIMIT 1
            """,
            (date,),
        ).fetchone()
        exact_match = True
        if row is None:
            row = conn.execute(
                """
                SELECT *
                FROM daily_summaries
                ORDER BY local_date DESC
                LIMIT 1
                """
            ).fetchone()
            exact_match = False
        if row is None:
            return None

        latest_row = conn.execute(
            """
            SELECT id, source, mode, status, started_at, finished_at, error
            FROM sync_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        webhook_status = {
            "last_processed_at": _get_sync_state(conn, "last_webhook_processed_at"),
            "last_failed_at": _get_sync_state(conn, "last_webhook_failed_at"),
            "last_failure_error": _get_sync_state(conn, "last_webhook_failure_error"),
        }
        auth_status = {
            "state": _derive_auth_state(conn),
            "token_source": _get_sync_state(conn, "auth_token_source"),
            "last_refresh_success_at": _get_sync_state(conn, "auth_last_refresh_success_at"),
            "last_refresh_failure_at": _get_sync_state(conn, "auth_last_refresh_failure_at"),
            "last_refresh_failure_reason": _get_sync_state(conn, "auth_last_refresh_failure_reason"),
            "last_api_success_at": _get_sync_state(conn, "auth_last_api_success_at"),
            "last_api_failure_at": _get_sync_state(conn, "auth_last_api_failure_at"),
            "last_api_failure_reason": _get_sync_state(conn, "auth_last_api_failure_reason"),
            "reauth_required": bool(_get_sync_state(conn, "auth_reauth_required", False)),
            "sync_blocked_by_auth": bool(_get_sync_state(conn, "auth_sync_blocked", False)),
        }
        latest_local_date = conn.execute("SELECT MAX(local_date) FROM daily_summaries").fetchone()[0]
        item_date = row["local_date"]
        freshness = _freshness_metadata(
            latest_stored_date=latest_local_date,
            item_date=item_date,
            last_sync_finished_at=latest_row["finished_at"] if latest_row else None,
            auth_status=auth_status,
            exact_match=exact_match,
        )
        return {
            "requested_date": date,
            "date": item_date,
            "source": "whoop_sqlite",
            "fallback_used": not exact_match,
            "latest_stored_date": latest_local_date,
            "recovery": {
                "score": row["recovery_score"],
                "hrv_ms": row["hrv_ms"],
                "rhr_bpm": row["rhr_bpm"],
                "spo2_pct": row["spo2_pct"],
                "skin_temp_c": row["skin_temp_celsius"],
            },
            "strain": {
                "day_strain": row["day_strain"],
                "kilojoules": row["day_kilojoules"],
                "avg_hr": row["day_avg_hr"],
                "max_hr": row["day_max_hr"],
            },
            "sleep": {
                "performance_pct": row["sleep_performance_pct"],
                "consistency_pct": _safe_number(row["sleep_consistency_pct"]),
                "efficiency_pct": row["sleep_efficiency_pct"],
                "total_hours": row["total_sleep_hours"],
                "light_hours": _safe_number(row["light_sleep_hours"]),
                "awake_hours": _safe_number(row["awake_hours"]),
                "in_bed_hours": _safe_number(row["in_bed_hours"]),
                "sws_hours": row["sws_hours"],
                "rem_hours": row["rem_hours"],
                "needed_hours": row["sleep_needed_baseline_hours"],
                "debt_hours": row["sleep_debt_hours"],
                "respiratory_rate": row["respiratory_rate"],
            },
            "workouts": _json_load(row["workouts_json"], []),
            "workout_zones": _json_load(_row_value(row, "workout_zone_json"), {}),
            "grappling_sessions": _json_load(_row_value(row, "grappling_sessions_json"), []),
            "manual_context": _json_load(_row_value(row, "manual_context_json"), []),
            "provenance": _json_load(_row_value(row, "provenance_json"), {}),
            "freshness": freshness,
            "auth": auth_status,
            "sync": {
                "last_successful_sync_at": latest_row["finished_at"] if latest_row and latest_row["status"] == "success" else None,
                "last_run": dict(latest_row) if latest_row else None,
                "last_webhook_processed_at": webhook_status["last_processed_at"],
                "last_webhook_failed_at": webhook_status["last_failed_at"],
                "last_webhook_failure_error": webhook_status["last_failure_error"],
            },
            "operator_action_needed": freshness["operator_action_needed"],
        }
    finally:
        conn.close()


def get_normalized_daily_from_api(date: str, tokens_path: str = WHOOP_TOKENS_FILE) -> dict[str, Any]:
    tokens = load_whoop_tokens(tokens_path)
    if not tokens:
        return {"error": "WHOOP auth failed", "auth": {"state": "expired"}}

    access_token = tokens.get("access_token")
    if not access_token:
        refreshed = refresh_whoop_tokens(tokens, tokens_path=tokens_path)
        access_token = refreshed.get("access_token") if refreshed else None
    if not access_token:
        return {"error": "WHOOP auth failed", "auth": {"state": "expired"}}

    try:
        recovery = fetch_paginated("/recovery", access_token)
        cycle = fetch_paginated("/cycle", access_token)
        sleep = fetch_paginated("/activity/sleep", access_token)
        workouts = fetch_paginated("/activity/workout", access_token)
    except requests.RequestException:
        refreshed = refresh_whoop_tokens(tokens, tokens_path=tokens_path)
        access_token = refreshed.get("access_token") if refreshed else None
        if not access_token:
            return {"error": "WHOOP auth failed", "auth": {"state": "expired"}}
        try:
            recovery = fetch_paginated("/recovery", access_token)
            cycle = fetch_paginated("/cycle", access_token)
            sleep = fetch_paginated("/activity/sleep", access_token)
            workouts = fetch_paginated("/activity/workout", access_token)
        except requests.RequestException:
            return {"error": "WHOOP auth failed", "auth": {"state": "expired"}}

    return {
        "date": date,
        "recovery": normalize_recovery(find_record_for_date(recovery, date)),
        "strain": normalize_cycle(find_record_for_date(cycle, date)),
        "sleep": normalize_sleep(find_record_for_date(sleep, date)),
        "workouts": [normalize_workout(item) for item in find_records_for_date(workouts, date)],
        "auth": {"state": "healthy"},
        "freshness": {"state": "live"},
    }


def _freshness_metadata(
    *,
    latest_stored_date: str | None,
    item_date: str,
    last_sync_finished_at: str | None,
    auth_status: dict[str, Any],
    exact_match: bool,
) -> dict[str, Any]:
    today = datetime.now(timezone.utc).date()
    stale_days = None
    state = "unknown"
    if latest_stored_date:
        latest_date = datetime.fromisoformat(latest_stored_date).date()
        stale_days = (today - latest_date).days
        state = "fresh" if stale_days <= 1 else "stale"
    operator_action_needed = auth_status.get("reauth_required") or (stale_days is not None and stale_days > 1)
    message_parts = []
    if latest_stored_date:
        message_parts.append(f"Latest stored WHOOP day: {latest_stored_date}")
    if stale_days is not None:
        message_parts.append(f"Freshness: {'stale' if stale_days > 1 else 'fresh'} by {stale_days} day(s)")
    if auth_status.get("state") not in {None, "healthy"}:
        message_parts.append(f"Live WHOOP API auth: {auth_status.get('state')}")
    if not exact_match:
        message_parts.append(f"Requested day unavailable; using latest stored day {item_date}")
    if operator_action_needed:
        message_parts.append("Suggested operator action: re-auth and resync")
    return {
        "state": state,
        "stale_days": stale_days,
        "last_successful_sync_at": last_sync_finished_at,
        "message": "; ".join(message_parts),
        "operator_action_needed": operator_action_needed,
        "exact_date_available": exact_match,
    }


def _derive_auth_state(conn: sqlite3.Connection) -> str:
    if _get_sync_state(conn, "auth_reauth_required", False):
        return "expired"
    if _get_sync_state(conn, "auth_sync_blocked", False):
        return "stale"
    if _get_sync_state(conn, "auth_last_api_success_at") or _get_sync_state(conn, "auth_last_refresh_success_at"):
        return "healthy"
    return "unknown"


def _get_sync_state(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value_text FROM sync_state WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    value = row["value_text"]
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _row_value(row: sqlite3.Row, key: str) -> Any:
    return row[key] if key in row.keys() else None


def _safe_number(value: Any) -> float | int | None:
    return value if isinstance(value, (int, float)) else None


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
        "kilojoules": first_number((item, score), "kilojoules", "kilojoule"),
        "avg_hr": first_number((item, score), "average_heart_rate", "avg_hr"),
        "max_hr": first_number((item, score), "max_heart_rate", "max_hr"),
    }


def normalize_sleep(item: dict[str, Any]) -> dict[str, Any]:
    score = item.get("score") or {}
    stage = score.get("stage_summary") or {}
    needed = score.get("sleep_needed") or {}
    return {
        "performance_pct": first_number((item, score), "sleep_performance_percentage", "performance_pct"),
        "consistency_pct": first_number((item, score), "sleep_consistency_percentage", "consistency_pct"),
        "efficiency_pct": first_number((item, score), "sleep_efficiency_percentage", "efficiency_pct"),
        "total_hours": seconds_to_hours(
            first_number((stage, score, item), "total_sleep_time_milli", "total_in_bed_time_milli")
        ),
        "light_hours": seconds_to_hours(first_number((stage, score, item), "total_light_sleep_time_milli", "light_sleep_time_milli")),
        "awake_hours": seconds_to_hours(first_number((stage, score, item), "total_awake_time_milli", "awake_time_milli")),
        "in_bed_hours": seconds_to_hours(first_number((stage, score, item), "total_in_bed_time_milli", "in_bed_time_milli")),
        "sws_hours": seconds_to_hours(first_number((stage, score, item), "total_slow_wave_sleep_time_milli", "slow_wave_sleep_time_milli", "sws_time_milli")),
        "rem_hours": seconds_to_hours(first_number((stage, score, item), "total_rem_sleep_time_milli", "rem_sleep_time_milli", "rem_time_milli")),
        "needed_hours": seconds_to_hours(first_number((needed, score, item), "baseline_milli", "sleep_needed_milli", "needed_sleep_milli")),
        "debt_hours": seconds_to_hours(first_number((needed, score, item), "need_from_sleep_debt_milli", "sleep_debt_milli", "debt_sleep_milli")),
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
    divisor = 3600000 if value > 10000 else 3600
    return round(float(value) / divisor, 2)


def minutes_from_seconds(value: float | int | None) -> int | None:
    if value is None:
        return None
    divisor = 60000 if value > 10000 else 60
    return int(round(float(value) / divisor))
