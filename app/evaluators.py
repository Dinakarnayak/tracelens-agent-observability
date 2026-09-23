import json
import re


def evaluate(evaluator: str, expected: str, actual: str) -> float:
    if evaluator == "exact_match":
        return float(expected.strip() == actual.strip())
    if evaluator == "contains":
        return float(expected.casefold() in actual.casefold())
    if evaluator == "json_valid":
        try:
            json.loads(actual)
            return 1.0
        except (json.JSONDecodeError, TypeError):
            return 0.0
    if evaluator == "keyword_coverage":
        words = set(re.findall(r"[\w'-]+", expected.casefold()))
        if not words:
            return 1.0
        actual_words = set(re.findall(r"[\w'-]+", actual.casefold()))
        return len(words & actual_words) / len(words)
    raise ValueError(f"Unsupported evaluator: {evaluator}")
