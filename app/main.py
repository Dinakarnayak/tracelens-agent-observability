from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from app import db
from app.evaluators import evaluate
from app.metrics import get_metrics
from app.schemas import EvaluationRequest, TraceSpan


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TraceLens Agent Reliability Workbench", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD


@app.post("/v1/traces", status_code=201)
def ingest_trace(span: TraceSpan):
    span_id = db.insert_span(span.model_dump())
    return {"id": span_id, "trace_id": span.trace_id, "run_id": span.run_id, "status": "stored"}


@app.get("/v1/traces")
def traces(limit: int = Query(default=100, ge=1, le=1000)):
    return {"items": db.list_spans(limit)}


@app.get("/v1/metrics")
def metrics(hours: int = Query(default=24, ge=1, le=720)):
    return get_metrics(hours)


@app.post("/v1/evaluations", status_code=201)
def run_evaluation(request: EvaluationRequest):
    results = []
    for case in request.cases:
        try:
            score = evaluate(request.evaluator, case.expected, case.actual)
            results.append({"case_id": case.id, "score": score, "passed": score >= 1.0})
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    score = sum(item["score"] for item in results) / len(results)
    evaluation_id, created_at = db.save_evaluation(request.name, request.evaluator, score, results)
    return {"id": evaluation_id, "name": request.name, "evaluator": request.evaluator,
            "score": score, "total": len(results), "results": results, "created_at": created_at}


@app.get("/v1/evaluations")
def evaluations(limit: int = Query(default=20, ge=1, le=200)):
    return {"items": db.list_evaluations(limit)}


DASHBOARD = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TraceLens</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#141b2e;--line:#25314a;--muted:#9aabc8;--text:#edf3ff;--accent:#66e3c4;--red:#ff7a90}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:38px 22px}header{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:26px}h1{font-size:27px;margin:0}h2{font-size:16px;margin:0 0 16px}.sub{color:var(--muted);margin:5px 0 0}.pill{border:1px solid var(--line);border-radius:99px;padding:7px 12px;color:var(--accent)}.cards{display:grid;grid-template-columns:repeat(5,minmax(130px,1fr));gap:12px}.card,section{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:18px}.label{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}.value{font-size:25px;font-weight:650;margin-top:8px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}section{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);white-space:nowrap}th{color:var(--muted);font-weight:550}.error{color:var(--red)}.empty{color:var(--muted);padding:16px 0}footer{color:var(--muted);font-size:12px;margin-top:18px}@media(max-width:800px){.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column}}
</style></head><body><main><header><div><h1>TraceLens</h1><p class="sub">Agent reliability · traces, latency, cost, evaluations</p></div><span class="pill" id="health">Connecting…</span></header>
<div class="cards" id="metrics"></div><div class="grid"><section><h2>Recent spans</h2><div id="traces"></div></section><section><h2>Evaluation runs</h2><div id="evals"></div></section></div><footer>Estimated model cost uses the editable price table in app/metrics.py. Unknown models are shown as $0.</footer></main>
<script>
const money=n=>'$'+Number(n||0).toFixed(4);const ms=n=>Number(n||0).toFixed(0)+' ms';
async function load(){try{const [m,t,e]=await Promise.all([fetch('/v1/metrics').then(r=>r.json()),fetch('/v1/traces?limit=12').then(r=>r.json()),fetch('/v1/evaluations?limit=10').then(r=>r.json())]);document.querySelector('#health').textContent='API healthy';const vals=[['Spans',m.span_count],['Error rate',(m.error_rate*100).toFixed(1)+'%'],['p95 latency',ms(m.p95_ms)],['Tokens',Number(m.input_tokens+m.output_tokens).toLocaleString()],['Estimated cost',money(m.estimated_cost_usd)]];document.querySelector('#metrics').innerHTML=vals.map(([a,b])=>`<div class="card"><div class="label">${a}</div><div class="value">${b}</div></div>`).join('');document.querySelector('#traces').innerHTML=t.items.length?`<table><thead><tr><th>Span</th><th>Type / model</th><th>Latency</th><th>Status</th></tr></thead><tbody>${t.items.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.span_type)} · ${esc(x.model||'—')}</td><td>${ms(x.duration_ms)}</td><td class="${x.status==='error'?'error':''}">${esc(x.status)}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">No traces yet. POST a span to /v1/traces.</div>';document.querySelector('#evals').innerHTML=e.items.length?`<table><thead><tr><th>Evaluation</th><th>Evaluator</th><th>Score</th><th>Cases</th></tr></thead><tbody>${e.items.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.evaluator)}</td><td>${(x.score*100).toFixed(1)}%</td><td>${x.total}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">No evaluations yet. Submit cases to /v1/evaluations.</div>'}catch(err){document.querySelector('#health').textContent='API unavailable'}}function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}load();setInterval(load,10000);
</script></body></html>"""
