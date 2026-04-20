import pytest

from app import read_logs, summarize


def test_summarize_detects_coverage_failures_and_flaky_tests():
    rows = [
        {"test_id": "T1", "status": "pass", "requirement_id": "REQ-1", "subsystem": "nvme", "failure_signature": ""},
        {"test_id": "T2", "status": "fail", "requirement_id": "REQ-2", "subsystem": "nvme", "failure_signature": "timeout"},
        {"test_id": "T2", "status": "pass", "requirement_id": "REQ-2", "subsystem": "nvme", "failure_signature": ""},
        {"test_id": "T3", "status": "blocked", "requirement_id": "REQ-3", "subsystem": "thermal", "failure_signature": ""},
    ]

    summary = summarize(rows)

    assert summary["total_tests"] == 4
    assert summary["pass_rate"] == 50.0
    assert summary["requirement_coverage"] == 66.67
    assert summary["top_failure_signatures"] == [("timeout", 1)]
    assert summary["flaky_tests"] == ["T2"]


def test_read_logs_rejects_unknown_status(tmp_path):
    csv_path = tmp_path / "logs.csv"
    csv_path.write_text(
        "test_id,status,requirement_id,subsystem,failure_signature\n"
        "T1,unknown,REQ-1,nvme,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        read_logs(csv_path)
