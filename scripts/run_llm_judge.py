"""Run a bounded OpenRouter judge evaluation and save actual structured results."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

import pandas as pd

from evaluation.llm_judge import JUDGE_JSON_SCHEMA, build_prompt, parse_judge_content
from scripts.run_spotify_agent import load_cases
from src.agent import run_agent
from src.intent_classifier import IntentClassifier
from src.retriever import TfidfRetriever


def load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def judge_request(prompt: str, model: str, api_key: str, *, json_schema: dict[str, object] | None = None) -> dict[str, object]:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 900,
        "response_format": (
            {"type": "json_schema", "json_schema": {"name": "support_judge", "strict": True, "schema": json_schema}}
            if json_schema
            else {"type": "json_object"}
        ),
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Hiver SDE Assignment",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not isinstance(content, str):
        raise ValueError("Judge response content must be text")
    return parse_judge_content(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--labels", default="data/golden/spotifycares_intent_golden.csv")
    parser.add_argument("--cases", default="data/processed/spotifycares_cases.jsonl")
    parser.add_argument("--output", default="reports/llm_judge_results.jsonl")
    parser.add_argument("--summary", default="reports/llm_judge_summary.json")
    parser.add_argument("--ids-file", default="", help="Optional CSV containing example_id/message_id to judge")
    parser.add_argument("--retries", type=int, default=0, help="Retries per example after an invalid/provider response")
    args = parser.parse_args()
    if not 1 <= args.limit <= 50 or args.retries < 0:
        raise ValueError("limit must be between 1 and 50")
    load_env(Path(".env"))
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not api_key or not model:
        raise ValueError(".env must contain LLM_API_KEY and LLM_MODEL")
    labels = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    if args.ids_file:
        ids_frame = pd.read_csv(args.ids_file, dtype=str, keep_default_na=False)
        id_column = "example_id" if "example_id" in ids_frame else "message_id"
        wanted = set(ids_frame[id_column].astype(str))
        labels = labels[labels["message_id"].astype(str).isin(wanted)]
    labels = labels.head(args.limit)
    classifier = IntentClassifier().fit(labels["customer_text"].tolist(), labels["intent"].tolist())
    cases = load_cases(Path(args.cases))
    retriever = TfidfRetriever().fit(cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    failures = 0
    calls = 0
    for row in labels.to_dict("records"):
        agent = run_agent(row["customer_text"], classifier, retriever)
        error_name = "UnknownError"
        for _ in range(args.retries + 1):
            calls += 1
            try:
                judged = judge_request(
                    build_prompt(row["customer_text"], agent["retrieved_cases"], str(agent["response_draft"]), str(agent["decision"])),
                    model,
                    api_key,
                    json_schema=JUDGE_JSON_SCHEMA,
                )
                rows.append({"message_id": row["message_id"], "judge": judged})
                break
            except Exception as error:
                error_name = type(error).__name__
        else:
            failures += 1
            rows.append({"message_id": row["message_id"], "error": error_name})
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    valid = [row["judge"] for row in rows if "judge" in row]
    scores = [value["score"] for result in valid for value in result.values()]
    summary = {
        "requested": len(labels),
        "successful": len(valid),
        "failed": failures,
        "api_calls_made": calls,
        "model": model,
        "mean_score_all_dimensions": sum(scores) / len(scores) if scores else None,
        "results": str(output),
        "human_agreement": "PENDING real human ratings",
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
