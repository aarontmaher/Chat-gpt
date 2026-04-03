from __future__ import annotations

import json

from parsers import whoop_proxy


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise whoop_proxy.requests.HTTPError("bad response")


def test_get_normalized_daily_returns_expected_schema(monkeypatch, tmp_path):
    tokens_path = tmp_path / "whoop_tokens.json"
    tokens_path.write_text(json.dumps({"access_token": "token"}), encoding="utf-8")

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/recovery"):
            return FakeResponse({"records": [{"date": "2026-04-02", "score": {"recovery_score": 36.0, "hrv_ms": 53.0, "rhr_bpm": 56, "spo2_pct": 94.8, "skin_temp_c": 33.8}}]})
        if url.endswith("/cycle"):
            return FakeResponse({"records": [{"date": "2026-04-02", "score": {"strain": 8.0, "kilojoules": 1200, "avg_hr": 85, "max_hr": 153}}]})
        if url.endswith("/activity/sleep"):
            return FakeResponse({"records": [{"date": "2026-04-02", "score": {"sleep_performance_percentage": 71.0, "sleep_efficiency_percentage": 92.6, "total_sleep_time_milli": 20556000, "slow_wave_sleep_time_milli": 7776000, "rem_sleep_time_milli": 4572000, "sleep_needed_milli": 27432000, "sleep_debt_milli": 6948000, "respiratory_rate": 14.2}}]})
        if url.endswith("/activity/workout"):
            return FakeResponse({"records": [{"date": "2026-04-02", "sport_id": 63, "duration_milli": 1620000, "score": {"strain": 6.27, "avg_hr": 120, "max_hr": 143}}]})
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(whoop_proxy.requests, "get", fake_get)

    result = whoop_proxy.get_normalized_daily("2026-04-02", tokens_path=str(tokens_path))

    assert result["date"] == "2026-04-02"
    assert result["recovery"]["score"] == 36.0
    assert result["strain"]["day_strain"] == 8.0
    assert result["sleep"]["total_hours"] == 5.71
    assert result["workouts"][0]["duration_min"] == 27


def test_get_normalized_daily_handles_missing_tokens_gracefully(tmp_path):
    result = whoop_proxy.get_normalized_daily("2026-04-02", tokens_path=str(tmp_path / "missing.json"))

    assert result == {"error": "WHOOP auth failed"}


def test_normalize_date_handles_iso_strings():
    assert whoop_proxy.normalize_date("2026-04-02") == "2026-04-02"
    assert whoop_proxy.normalize_date("2026-04-02T12:30:00Z") == "2026-04-02"
