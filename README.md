# Validation Test Log Analyzer

A small Python validation/testing project that turns hardware or software test logs into coverage, failure, and triage reports.

## Why It Matches Validation / Test Jobs

- Shows test-plan thinking: test cases, requirements, expected results, pass/fail status
- Produces coverage metrics by subsystem and requirement
- Groups failures by signature for faster debug and root-cause triage
- Generates structured JSON and readable HTML reports
- Uses Python automation, CSV inputs, and repeatable command-line execution

## Features

- Parse validation test logs from CSV
- Calculate pass rate, fail rate, blocked tests, and skipped tests
- Report requirement coverage and subsystem coverage
- Identify top failing tests and common failure signatures
- Flag flaky tests when the same test has both pass and fail outcomes
- Export JSON summary and HTML report

## Run

```powershell
python app.py --input samples/validation_logs.csv --out report
```

Outputs:

- `report/validation-summary.json`
- `report/validation-report.html`

## Resume Bullets

- Built a Python validation log analyzer that parses test results, computes pass/fail/blocked rates, and reports requirement coverage by subsystem.
- Implemented failure triage logic that groups failures by signature, highlights flaky tests, and identifies top failing validation cases.
- Generated JSON and HTML reports to make validation status, test coverage, and debug priorities easier for engineering review.

## GitHub Reminder

Push this project to GitHub before using it as a resume link.

