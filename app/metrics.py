from datetime import datetime, timedelta, timezone
from app.db import connect

# USD per million tokens; adjust to your provider/model pricing.
MODEL_PRICES = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "claude-sonnet-4": (3.00, 15.00),
}


def get_metrics(hours: int):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with connect() as db:
        rows = db.execute("SELECT model,status,duration_ms,input_tokens,output_tokens FROM spans WHERE created_at >= ?", (cutoff,)).fetchall()
    groups = {}
    latencies = []
    errors = 0
    tokens_in = tokens_out = 0
    cost = 0.0
    for row in rows:
        model = row["model"] or "unknown"
        item = groups.setdefault(model, {"spans": 0, "errors": 0, "input_tokens": 0, "output_tokens": 0, "latencies_ms": []})
        item["spans"] += 1
        item["errors"] += int(row["status"] == "error")
        item["input_tokens"] += row["input_tokens"]
        item["output_tokens"] += row["output_tokens"]
        item["latencies_ms"].append(row["duration_ms"])
        latencies.append(row["duration_ms"])
        errors += int(row["status"] == "error")
        tokens_in += row["input_tokens"]
        tokens_out += row["output_tokens"]
        input_rate, output_rate = MODEL_PRICES.get(model, (0.0, 0.0))
        cost += (row["input_tokens"] * input_rate + row["output_tokens"] * output_rate) / 1_000_000
    def percentile(values, p):
        if not values:
            return 0.0
        ordered = sorted(values)
        return float(ordered[min(len(ordered)-1, round((len(ordered)-1)*p))])
    by_model = {}
    for model, item in groups.items():
        values = item.pop("latencies_ms")
        by_model[model] = {**item, "p50_ms": percentile(values, .50), "p95_ms": percentile(values, .95)}
    return {"window_hours": hours, "span_count": len(rows), "error_count": errors,
            "error_rate": errors / len(rows) if rows else 0.0,
            "p50_ms": percentile(latencies, .50), "p95_ms": percentile(latencies, .95),
            "input_tokens": tokens_in, "output_tokens": tokens_out,
            "estimated_cost_usd": round(cost, 6), "by_model": by_model}
