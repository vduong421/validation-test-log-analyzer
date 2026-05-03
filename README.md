# Validation Test Log Analyzer

Validation Test Log Analyzer is a local triage tool that parses hardware/software test logs, groups failures by signature, calculates coverage and pass/fail status, and uses local AI to explain the validation result.

The deterministic analyzer produces auditable metrics; the AI triage copilot turns those metrics into a concise debug plan.

## What It Does

- Parses raw validation test logs.
- Extracts pass/fail status, subsystem, error signature, and coverage information.
- Groups recurring failures and highlights flaky patterns.
- Generates JSON and Markdown summaries.
- Adds AI triage analysis for hardware/software validation review.

## AI Features

- Local AI triage copilot explains the dominant failure pattern.
- AI output recommends likely owner, next debug action, and release risk.
- Recommendations are grounded in parsed log metrics.
- The app can run deterministic analysis even when AI is not available.

## Architecture

```text
Raw validation logs
      |
      v
Log parser -> failure grouping -> coverage/pass-fail metrics
      |
      v
Local AI triage copilot -> debug plan + risk summary
      |
      v
JSON / Markdown output
```

## Run

```powershell
run.bat
```

## Local AI Setup

Use LM Studio or another local OpenAI-compatible server with a small model such as `google/gemma-4-e4b`.

## Main Files

- `app.py` - parser, summary generation, and AI triage prompt.
- `samples/` - validation log samples.
- `agents/Agent.md` - validation triage copilot instructions.

## Output

The analyzer returns pass/fail counts, failure groups, coverage status, AI triage notes, and recommended next debug actions.
