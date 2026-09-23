from typing import Any, Literal
from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    trace_id: str = Field(min_length=1, max_length=160)
    run_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=200)
    span_type: Literal["agent", "llm", "tool", "retrieval", "other"] = "other"
    model: str | None = Field(default=None, max_length=160)
    duration_ms: float = Field(ge=0, le=86_400_000)
    status: Literal["ok", "error"] = "ok"
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    input: str | None = Field(default=None, max_length=20000)
    output: str | None = Field(default=None, max_length=20000)
    attributes: dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    expected: str
    actual: str


class EvaluationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    evaluator: Literal["exact_match", "contains", "json_valid", "keyword_coverage"]
    cases: list[EvalCase] = Field(min_length=1, max_length=1000)
