# TraceLens — Agent Reliability Workbench

TraceLens is a lightweight, self-hostable observability and evaluation workbench for AI agents. Ingest structured spans, inspect latency, errors, token use, and estimated cost, then run repeatable checks against model outputs.

## Why this project

AI agent systems are moving into production, and teams need evidence about both runtime behavior and output quality. TraceLens focuses on the engineering feedback loop: capture a run, see where it failed or spent time, and evaluate output changes against explicit cases.

## Features

- FastAPI ingestion endpoint for agent and LLM spans.
- SQLite storage with a normalized span schema.
- Metrics by model: calls, errors, p50/p95 latency, token totals, and estimated cost.
- Dataset-style evaluation API with deterministic exact-match, contains, JSON-validity, and keyword-coverage evaluators.
- Lightweight dashboard at `/` with recent traces, metrics, and evaluations.
- Docker setup; no external services required.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000. API docs are at `/docs`.

## Send a trace

```bash
curl -X POST http://localhost:8000/v1/traces \
  -H 'Content-Type: application/json' \
  -d '{"trace_id":"demo-001","run_id":"run-001","name":"answer_question","span_type":"agent","model":"gpt-4.1-mini","duration_ms":842,"status":"ok","input_tokens":120,"output_tokens":84,"input":"What is observability?","output":"Observability helps explain system behavior from its outputs."}'
```

Get model and run metrics from `GET /v1/metrics`; recent spans from `GET /v1/traces`.

## Evaluate a dataset

```bash
curl -X POST http://localhost:8000/v1/evaluations \
  -H 'Content-Type: application/json' \
  -d '{"name":"support-answer-regression","evaluator":"keyword_coverage","cases":[{"id":"case-1","expected":"refund policy within 30 days","actual":"Our refund policy allows returns within 30 days."}]}'
```

Supported evaluators: `exact_match`, `contains`, `json_valid`, and `keyword_coverage`. Evaluation results are stored and returned with per-case scores.

## API

- `POST /v1/traces` — ingest one span.
- `GET /v1/traces?limit=100` — list recent spans.
- `GET /v1/metrics?hours=24` — aggregate run quality, latency, tokens, and cost.
- `POST /v1/evaluations` — evaluate a named set of cases.
- `GET /v1/evaluations?limit=20` — list evaluation runs.
- `GET /health` — health check.

## Cost estimates

Cost is an estimate using the small editable price table in `app/metrics.py`. Update the per-million-token rates for the models you use. Unknown models report zero estimated cost rather than inventing a price.

## Production next steps

Add API authentication and tenant isolation before exposing the service; move SQLite to PostgreSQL; export OpenTelemetry GenAI semantic conventions; add online sampling and human feedback; and compare evaluation scores across prompt/model versions. TraceLens is a starter project, not a drop-in production monitoring service.
