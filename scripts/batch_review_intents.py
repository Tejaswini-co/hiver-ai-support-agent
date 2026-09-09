"""Batch human review for provisional SpotifyCares intent suggestions.

Provisional labels are never promoted silently. Each batch is printed and the
reviewer must explicitly approve it or provide corrections before rows become
HUMAN_REVIEWED.
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

from scripts.review_intents import APPROVED_INTENTS


def atomic_write(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        writer = csv.DictWriter(temporary, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames or []
        rows = list(reader)
    required = {"message_id", "conversation_id", "customer_text", "provisional_intent", "provisional_reason"}
    missing = required.difference(fields)
    if missing:
        raise ValueError(f"Missing required provisional columns: {sorted(missing)}")
    if len(rows) != 200:
        raise ValueError(f"Expected exactly 200 provisional rows, found {len(rows)}")
    return fields, rows


def initialize_output(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for row in rows:
        result.append({
            "message_id": row["message_id"],
            "conversation_id": row["conversation_id"],
            "customer_text": row["customer_text"],
            "intent": "",
            "label_notes": "",
            "review_status": "PENDING",
            "provisional_intent": row["provisional_intent"],
            "provisional_reason": row["provisional_reason"],
        })
    return result


def print_batch(rows: list[dict[str, str]], start: int, end: int) -> None:
    print(f"\n{'=' * 100}\nBatch rows {start + 1}-{end} of 200")
    for index in range(start, end):
        row = rows[index]
        print(f"\n[{index + 1}] message_id={row['message_id']} conversation_id={row['conversation_id']}")
        print(f"Customer: {row['customer_text']}")
        print(f"AI suggestion: {row['provisional_intent']} ({row.get('provisional_confidence', 'n/a')})")
        print(f"Reason: {row['provisional_reason']}")


def parse_corrections(raw: str, batch_start: int, batch_end: int) -> dict[int, tuple[str, str]]:
    """Parse `global_number=intent|reason,...` corrections."""
    corrections: dict[int, tuple[str, str]] = {}
    if not raw.strip():
        return corrections
    for item in raw.split(","):
        if "=" not in item or "|" not in item:
            raise ValueError("Correction format: number=intent|short reason")
        number_text, value = item.strip().split("=", 1)
        intent, reason = value.split("|", 1)
        number = int(number_text)
        if not batch_start <= number <= batch_end:
            raise ValueError(f"Correction {number} is outside the current batch")
        if intent not in APPROVED_INTENTS:
            raise ValueError(f"Invalid intent: {intent}")
        if not reason.strip():
            raise ValueError(f"Correction {number} needs a reason")
        corrections[number - 1] = (intent, reason.strip())
    return corrections


def summary(rows: list[dict[str, str]]) -> dict[str, int]:
    reviewed = [row for row in rows if row["review_status"] == "HUMAN_REVIEWED"]
    corrected = [
        row for row in reviewed
        if row["intent"] != row["provisional_intent"]
    ]
    return {
        "total": len(rows),
        "approved_unchanged": len(reviewed) - len(corrected),
        "corrected": len(corrected),
        "still_pending": len(rows) - len(reviewed),
    }


def write_summary(path: Path, values: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Batch Intent Review Summary\n\n"
        "These counts describe the current human-review state. Provisional labels are not counted as reviewed.\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in values.items())
        + "\n",
        encoding="utf-8",
    )


def run(provisional_path: Path, output_path: Path, summary_path: Path, batch_size: int) -> None:
    _, provisional = load_rows(provisional_path)
    if output_path.exists():
        with output_path.open("r", newline="", encoding="utf-8") as source:
            final_rows = list(csv.DictReader(source))
        if len(final_rows) != 200:
            raise ValueError(f"Existing output must contain 200 rows: {output_path}")
    else:
        final_rows = initialize_output(provisional)
        atomic_write(output_path, list(final_rows[0]), final_rows)

    fields = list(final_rows[0])
    for start in range(0, len(final_rows), batch_size):
        end = min(start + batch_size, len(final_rows))
        if all(row["review_status"] == "HUMAN_REVIEWED" for row in final_rows[start:end]):
            continue
        print_batch(provisional, start, end)
        print("\nReview action: approve = accept all suggestions; corrections = enter comma-separated corrections")
        print("Correction format: global_number=intent|short reason")
        print("Commands: a=approve all in batch, c=corrections then approve remaining, q=save and quit")
        while True:
            action = input("Batch action: ").strip()
            if action.lower() == "q":
                atomic_write(output_path, fields, final_rows)
                write_summary(summary_path, summary(final_rows))
                print(f"Saved progress to {output_path}")
                return
            if action.lower() == "a":
                corrections = {}
                break
            if action.lower() == "c":
                try:
                    corrections = parse_corrections(input("Corrections (blank for none): "), start + 1, end)
                except (ValueError, TypeError) as error:
                    print(f"Invalid corrections: {error}")
                    continue
                break
            print("Use a, c, or q.")
        for index in range(start, end):
            provisional_row = provisional[index]
            final_rows[index]["intent"] = provisional_row["provisional_intent"]
            final_rows[index]["label_notes"] = f"Human-approved unchanged suggestion. {provisional_row['provisional_reason']}"
            if index in corrections:
                final_rows[index]["intent"], final_rows[index]["label_notes"] = corrections[index]
            final_rows[index]["review_status"] = "HUMAN_REVIEWED"
        atomic_write(output_path, fields, final_rows)
        write_summary(summary_path, summary(final_rows))
        print(f"Saved batch. Current summary: {summary(final_rows)}")
    print(f"All batches reviewed. Final golden CSV: {output_path}")
    print(f"Summary: {summary(final_rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review provisional intent labels in batches.")
    parser.add_argument("--provisional", default="data/golden/spotifycares_intent_provisional_review.csv")
    parser.add_argument("--output", default="data/golden/spotifycares_intent_golden.csv")
    parser.add_argument("--summary", default="reports/intent_batch_review_summary.md")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 200:
        raise ValueError("batch-size must be between 1 and 200")
    run(Path(args.provisional), Path(args.output), Path(args.summary), args.batch_size)


if __name__ == "__main__":
    main()