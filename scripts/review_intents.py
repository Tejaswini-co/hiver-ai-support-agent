"""Interactive human-review workflow for the SpotifyCares intent CSV."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from pathlib import Path


APPROVED_INTENTS = (
    "playback_audio_issue",
    "app_technical_issue",
    "account_access",
    "subscription_plan_billing",
    "playlist_library_downloads",
    "device_platform_compatibility",
    "feature_or_policy_information",
    "other_unclear",
)

KEYWORDS = {
    "playback_audio_issue": ("song", "music", "shuffle", "repeat", "sound", "playback", "pause", "skip", "audio", "listen"),
    "app_technical_issue": ("app", "crash", "error", "bug", "work", "working", "update", "loading", "doesn't work", "not work", "issue", "problem"),
    "account_access": ("login", "log in", "logged", "password", "account", "email", "access", "sign in", "facebook login"),
    "subscription_plan_billing": ("premium", "subscription", "payment", "charge", "refund", "billing", "price", "student discount", "plan"),
    "playlist_library_downloads": ("playlist", "album", "library", "download", "offline", "saved", "local file", "greyed"),
    "device_platform_compatibility": ("iphone", "ios", "android", "windows", "mac", "browser", "device", "desktop", "phone", "speaker"),
    "feature_or_policy_information": ("feature", "possible", "available", "how do", "can i", "suggestion", "why", "is there a way"),
}

INTENT_WEIGHTS = {
    "other_unclear": 0,
}


def propose_details(customer_text: str) -> tuple[str, str, float, list[str]]:
    """Produce a transparent provisional suggestion; never represents human review."""
    lowered = customer_text.lower()
    matched_by_intent = {
        intent: [
            keyword
            for keyword in keywords
            if (keyword in {"doesn't work", "not work", "issue", "problem", "how do", "can i", "facebook login", "student discount", "local file", "is there a way"}
                and keyword in lowered)
            or (keyword not in {"doesn't work", "not work", "issue", "problem", "how do", "can i", "facebook login", "student discount", "local file", "is there a way"}
                and re.search(rf"\b{re.escape(keyword)}\b", lowered))
        ]
        for intent, keywords in KEYWORDS.items()
    }
    scores = {intent: len(matches) for intent, matches in matched_by_intent.items()}
    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    ranked = sorted(scores.values(), reverse=True)
    second_score = ranked[1] if len(ranked) > 1 else 0
    if best_score == 0:
        return "other_unclear", "No taxonomy signal was detected; human review is required.", 0.20, []
    if best_score == second_score:
        tied = [intent for intent, score in scores.items() if score == best_score]
        return "other_unclear", f"Signals are tied between: {', '.join(tied)}; human review is required.", 0.30, matched_by_intent[best_intent]
    confidence = min(0.95, 0.50 + 0.12 * best_score + 0.08 * (best_score - second_score))
    reason = f"Matched signals for {best_intent}: {', '.join(matched_by_intent[best_intent])}."
    return best_intent, reason, round(confidence, 2), matched_by_intent[best_intent]


def propose_intent(customer_text: str) -> tuple[str, str]:
    """Return a review suggestion only; this function never writes a label."""
    intent, reason, _, _ = propose_details(customer_text)
    return intent, reason


def save_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Atomically save after each human decision without changing message fields."""
    directory = path.parent
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=directory, delete=False) as temporary:
        writer = csv.DictWriter(temporary, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def review(path: Path) -> None:
    with path.open("r", newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    required = {"message_id", "conversation_id", "customer_text", "intent", "label_notes"}
    missing = required.difference(fieldnames)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if len(rows) != 200:
        raise ValueError(f"Expected exactly 200 rows, found {len(rows)}")

    print("Human intent review")
    print("Commands: Enter/y=approve suggestion, 1-8=choose intent, s=skip, q=save and quit")
    for index, row in enumerate(rows):
        if row["intent"].strip():
            continue
        suggestion, reason = propose_intent(row["customer_text"])
        print(f"\nExample {index + 1}/200 | message_id={row['message_id']} | conversation_id={row['conversation_id']}")
        print(f"Customer: {row['customer_text']}")
        print(f"Suggested intent: {suggestion}")
        print(f"Reason: {reason}")
        for number, intent in enumerate(APPROVED_INTENTS, start=1):
            print(f"  {number}. {intent}")
        while True:
            choice = input("Approve suggestion, choose 1-8, s=skip, q=quit: ").strip().lower()
            if choice in {"", "y"}:
                selected = suggestion
                note = f"Human-approved suggestion. {reason}"
                break
            if choice.isdigit() and 1 <= int(choice) <= len(APPROVED_INTENTS):
                selected = APPROVED_INTENTS[int(choice) - 1]
                note = input("Short label reason: ").strip()
                if not note:
                    print("A short reason is required.")
                    continue
                break
            if choice == "s":
                print("Skipped; this row remains unlabeled.")
                break
            if choice == "q":
                save_rows(path, fieldnames, rows)
                print(f"Saved progress to {path}")
                return
            print("Enter, y, a number from 1-8, s, or q.")
        if choice == "s":
            continue
        row["intent"] = selected
        row["label_notes"] = note
        save_rows(path, fieldnames, rows)
        print(f"Saved {selected} for message_id={row['message_id']}")
    print(f"Review complete. Saved {path}")


def provisional_review(path: Path, output_path: Path, report_path: Path) -> None:
    """Create a separate AI-suggestion artifact for compact human review."""
    with path.open("r", newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        source_fields = reader.fieldnames or []
        rows = list(reader)
    required = {"message_id", "conversation_id", "customer_text"}
    missing = required.difference(source_fields)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if len(rows) != 200:
        raise ValueError(f"Expected exactly 200 rows, found {len(rows)}")

    fields = source_fields + ["provisional_intent", "provisional_reason", "provisional_confidence", "human_review_status"]
    provisional_rows: list[dict[str, str]] = []
    distribution: dict[str, int] = {}
    low_confidence = 0
    report_lines = [
        "# SpotifyCares Provisional Intent Review",
        "",
        "These are AI-suggested provisional labels, not hand-labelled evaluation data.",
        "Human review is required before copying any labels into the golden CSV or training.",
        "",
        "| # | Message ID | Provisional intent | Confidence | Customer message | Reason |",
        "|---:|---|---|---:|---|---|",
    ]
    for index, row in enumerate(rows, start=1):
        intent, reason, confidence, _ = propose_details(row["customer_text"])
        output_row = dict(row)
        output_row.update({
            "provisional_intent": intent,
            "provisional_reason": reason,
            "provisional_confidence": str(confidence),
            "human_review_status": "PENDING",
        })
        provisional_rows.append(output_row)
        distribution[intent] = distribution.get(intent, 0) + 1
        if confidence < 0.50 or intent == "other_unclear":
            low_confidence += 1
        safe_text = row["customer_text"].replace("|", "\\|").replace("\n", " ")
        report_lines.append(f"| {index} | {row['message_id']} | `{intent}` | {confidence:.2f} | {safe_text} | {reason} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_rows(output_path, fields, provisional_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "PROVISIONAL_AI_SUGGESTIONS_PENDING_HUMAN_REVIEW",
        "examples": len(rows),
        "distribution": distribution,
        "low_confidence_or_unclear": low_confidence,
        "source": str(path),
        "provisional_file": str(output_path),
        "human_review_required": True,
    }
    report_lines.extend([
        "",
        "## Summary",
        "",
        f"- Examples: {len(rows)}",
        f"- Low-confidence or unclear: {low_confidence}",
        f"- Distribution: `{json.dumps(distribution, sort_keys=True)}`",
        "- Status: **PROVISIONAL; NOT HAND-LABELLED**",
    ])
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Review SpotifyCares intent labels one example at a time.")
    parser.add_argument("--labels", default="data/golden/spotifycares_intent_candidates.csv")
    parser.add_argument("--provisional", action="store_true", help="Create AI suggestions without changing the source CSV")
    parser.add_argument("--output", default="data/golden/spotifycares_intent_provisional_review.csv")
    parser.add_argument("--report", default="reports/provisional_intent_review.md")
    args = parser.parse_args()
    if args.provisional:
        provisional_review(Path(args.labels), Path(args.output), Path(args.report))
    else:
        review(Path(args.labels))


if __name__ == "__main__":
    main()