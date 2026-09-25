from datetime import date
import pytest
from services.orchestrator.traffic_execution import _effective_month_filter, _temporal_window, TrafficProblem, _fallback_traffic_answer


class Cursor:
    def __init__(self, months, sources=("AIS",)):
        self.months, self.sources = months, sources
    def execute(self, sql, params):
        self.sql, self.params = sql, params
    def fetchone(self):
        return {"min_month": date(2020, 1, 1), "max_month": date(2020, 12, 1), "months": self.months}
    def fetchall(self):
        return [{"layer_source": source, "month": month} for source in self.sources for month in self.months]


def test_recent_period_does_not_silently_use_old_loaded_data():
    with pytest.raises(TrafficProblem) as error:
        _effective_month_filter(Cursor(["202012"]), ["AIS"], _temporal_window("최근 12개월 AIS 통항량"))
    assert error.value.code == "TRAFFIC_PERIOD_NOT_COVERED"


def test_explicit_loaded_three_months_is_parameterized_and_bounded():
    sql, metadata = _effective_month_filter(Cursor(["202010", "202011", "202012"]), ["AIS"], _temporal_window("적재 자료 최근 3개월 AIS 통항량"))
    assert "start_month" in sql
    assert metadata["start_month"] == "2020-10-01"
    assert metadata["max_month"] == "2020-12-01"
    assert len(metadata["effective_temporal_window"]["available_months"]) == 3


def test_each_requested_source_must_cover_period():
    with pytest.raises(TrafficProblem) as error:
        _effective_month_filter(Cursor(["202012"]), ["AIS", "V-PASS"], _temporal_window("최신 적재 월"))
    assert error.value.code == "TRAFFIC_PERIOD_NOT_COVERED"


def test_daily_request_not_misrepresented_as_monthly():
    with pytest.raises(TrafficProblem) as error:
        _effective_month_filter(Cursor(["202012"]), ["AIS"], _temporal_window("최근 7일 AIS 통항량"))
    assert error.value.code == "MONTHLY_RESOLUTION_ONLY"


def test_answer_does_not_invent_dominant_source_or_twelve_month_window():
    answer = _fallback_traffic_answer({"analysis_scope": {"period": "202012", "interpretation": "latest_loaded_calendar_months"}, "source_totals": {"AIS": 100, "V-PASS": 0}})
    assert "비중이 더 크게" not in answer
    assert "12개월" not in answer
    assert "고유 선박 수가 아닙니다" in answer
