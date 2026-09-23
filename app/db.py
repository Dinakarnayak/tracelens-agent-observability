import json
import sqlite3
from datetime import datetime, timezone
from app.config import DATABASE_PATH


def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS spans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT NOT NULL,
            run_id TEXT NOT NULL, name TEXT NOT NULL, span_type TEXT NOT NULL,
            model TEXT, duration_ms REAL NOT NULL, status TEXT NOT NULL,
            input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
            input_text TEXT, output_text TEXT, attributes_json TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_spans_created ON spans(created_at DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_spans_run ON spans(run_id)")
        db.execute("""CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            evaluator TEXT NOT NULL, score REAL NOT NULL, total INTEGER NOT NULL,
            results_json TEXT NOT NULL, created_at TEXT NOT NULL)""")


def insert_span(span: dict):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cursor = db.execute("""INSERT INTO spans(
            trace_id, run_id, name, span_type, model, duration_ms, status,
            input_tokens, output_tokens, input_text, output_text, attributes_json, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (span["trace_id"], span["run_id"], span["name"], span["span_type"], span.get("model"),
         span["duration_ms"], span["status"], span["input_tokens"], span["output_tokens"],
         span.get("input"), span.get("output"), json.dumps(span.get("attributes", {})), now))
        return cursor.lastrowid


def list_spans(limit: int):
    with connect() as db:
        rows = db.execute("SELECT * FROM spans ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def save_evaluation(name: str, evaluator: str, score: float, results: list[dict]):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cursor = db.execute("INSERT INTO evaluations(name,evaluator,score,total,results_json,created_at) VALUES(?,?,?,?,?,?)",
                            (name, evaluator, score, len(results), json.dumps(results), now))
        return cursor.lastrowid, now


def list_evaluations(limit: int):
    with connect() as db:
        rows = db.execute("SELECT * FROM evaluations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["results"] = json.loads(item.pop("results_json"))
        result.append(item)
    return result
