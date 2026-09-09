"""Create an unlabeled, thread-aware candidate file for manual annotation."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.intent_data import spotify_customer_messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/twcs.csv")
    parser.add_argument("--output", default="data/golden/spotifycares_intent_candidates.csv")
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    messages = spotify_customer_messages(args.input)
    if args.size > len(messages):
        raise ValueError(f"Requested {args.size} rows, only {len(messages)} are available")
    sample = messages.sample(n=args.size, random_state=args.seed).copy()
    sample["intent"] = ""
    sample["label_notes"] = ""
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(output, index=False)
    print(f"Wrote {len(sample)} unlabeled candidates to {output}")
    print("No labels or evaluation results were generated.")


if __name__ == "__main__":
    main()