import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

SHARED = Path(__file__).resolve().parents[1] / "_shared_project_workbench"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from local_llm import chat_json


STATUSES = {"pass", "fail", "blocked", "skip"}


def read_logs(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["status"] = row["status"].strip().lower()
        if row["status"] not in STATUSES:
            raise ValueError(f"Unknown status {row['status']} for test {row['test_id']}")
    return rows


def percent(part, whole):
    return round((part / whole) * 100, 2) if whole else 0.0


def summarize(rows):
    total = len(rows)
    status_counts = Counter(row["status"] for row in rows)
    requirements = {row["requirement_id"] for row in rows}
    covered_requirements = {
        row["requirement_id"]
        for row in rows
        if row["status"] in {"pass", "fail"}
    }

    by_subsystem = defaultdict(lambda: Counter())
    history_by_test = defaultdict(set)
    failure_signatures = Counter()
    failing_tests = Counter()

    for row in rows:
        by_subsystem[row["subsystem"]][row["status"]] += 1
        history_by_test[row["test_id"]].add(row["status"])
        if row["status"] == "fail":
            signature = row["failure_signature"] or "unspecified"
            failure_signatures[signature] += 1
            failing_tests[row["test_id"]] += 1

    flaky_tests = sorted(
        test_id for test_id, statuses in history_by_test.items()
        if "pass" in statuses and "fail" in statuses
    )

    subsystem_summary = {}
    for subsystem, counts in sorted(by_subsystem.items()):
        subtotal = sum(counts.values())
        subsystem_summary[subsystem] = {
            "total": subtotal,
            "pass": counts["pass"],
            "fail": counts["fail"],
            "blocked": counts["blocked"],
            "skip": counts["skip"],
            "pass_rate": percent(counts["pass"], subtotal),
        }

    return {
        "total_tests": total,
        "status_counts": dict(status_counts),
        "pass_rate": percent(status_counts["pass"], total),
        "fail_rate": percent(status_counts["fail"], total),
        "blocked_rate": percent(status_counts["blocked"], total),
        "requirements_total": len(requirements),
        "requirements_covered": len(covered_requirements),
        "requirement_coverage": percent(len(covered_requirements), len(requirements)),
        "subsystems": subsystem_summary,
        "top_failure_signatures": failure_signatures.most_common(5),
        "top_failing_tests": failing_tests.most_common(5),
        "flaky_tests": flaky_tests,
    }


def write_html(summary, output_path):
    subsystem_rows = "\n".join(
        f"<tr><td>{name}</td><td>{data['total']}</td><td>{data['pass']}</td>"
        f"<td>{data['fail']}</td><td>{data['blocked']}</td><td>{data['pass_rate']}%</td></tr>"
        for name, data in summary["subsystems"].items()
    )
    failures = "\n".join(
        f"<li>{signature}: {count}</li>"
        for signature, count in summary["top_failure_signatures"]
    ) or "<li>No failures</li>"
    flaky = "\n".join(f"<li>{test_id}</li>" for test_id in summary["flaky_tests"]) or "<li>No flaky tests detected</li>"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Validation Test Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; }}
    h1, h2 {{ color: #0f766e; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; }}
    .card strong {{ display: block; font-size: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>Validation Test Report</h1>
  <section class="cards">
    <div class="card"><span>Total Tests</span><strong>{summary['total_tests']}</strong></div>
    <div class="card"><span>Pass Rate</span><strong>{summary['pass_rate']}%</strong></div>
    <div class="card"><span>Fail Rate</span><strong>{summary['fail_rate']}%</strong></div>
    <div class="card"><span>Requirement Coverage</span><strong>{summary['requirement_coverage']}%</strong></div>
  </section>
  <h2>Subsystem Coverage</h2>
  <table>
    <tr><th>Subsystem</th><th>Total</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>Pass Rate</th></tr>
    {subsystem_rows}
  </table>
  <h2>Top Failure Signatures</h2>
  <ul>{failures}</ul>
  <h2>Flaky Tests</h2>
  <ul>{flaky}</ul>
</body>
</html>"""
    Path(output_path).write_text(html, encoding="utf-8")


def generate_ai_triage(summary, model):
    prompt = f"""You are a validation triage copilot for hardware/software test teams.

Return only valid JSON with keys:
- executive_summary
- likely_hotspots (array of 3 short bullets)
- next_debug_actions (array of 3 short bullets)
- review_note

Rules:
- stay grounded in the structured summary
- emphasize subsystem, failure signature, and flaky-test patterns
- keep bullets short and practical

Structured validation summary:
{json.dumps(summary, indent=2)}
"""
    return chat_json(prompt, model=model)


def main():
    parser = argparse.ArgumentParser(description="Summarize validation test logs.")
    parser.add_argument("--input", required=True, help="CSV validation log path")
    parser.add_argument("--out", default="report", help="Output directory")
    parser.add_argument("--use-ai", action="store_true")
    parser.add_argument("--model", default="google/gemma-4-e4b")
    args = parser.parse_args()

    rows = read_logs(args.input)
    summary = summarize(rows)
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "validation-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_html(summary, output_dir / "validation-report.html")
    if args.use_ai:
        ai = generate_ai_triage(summary, args.model)
        (output_dir / "validation-ai-brief.json").write_text(json.dumps(ai, indent=2), encoding="utf-8")
        ai_md = [
            "# AI Validation Triage Brief",
            "",
            ai["executive_summary"],
            "",
            "## Likely Hotspots",
            *[f"- {item}" for item in ai.get("likely_hotspots", [])],
            "",
            "## Next Debug Actions",
            *[f"- {item}" for item in ai.get("next_debug_actions", [])],
            "",
            f"## Review Note\n- {ai.get('review_note', '')}",
        ]
        (output_dir / "validation-ai-brief.md").write_text("\n".join(ai_md) + "\n", encoding="utf-8")
        summary["ai_copilot"] = ai
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

