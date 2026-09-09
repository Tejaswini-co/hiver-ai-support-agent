"""Run the reproducible local evaluation artifacts that require no external API."""

from __future__ import annotations

import argparse
import subprocess
import sys


def run(module: str, *arguments: str) -> None:
    command = [sys.executable, "-m", module, *arguments]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default="data/golden/spotifycares_intent_golden.csv")
    parser.add_argument("--build-cases", action="store_true")
    args = parser.parse_args()
    if args.build_cases:
        run("scripts.build_spotify_cases")
    run("scripts.validate_intent_labels", "--labels", args.labels)
    run("scripts.train_intent", "--labels", args.labels)
    run("scripts.evaluate_baselines", "--labels", args.labels)
    print("Local evaluation complete. LLM-judge and human-agreement runs remain separate because they require real external ratings.")


if __name__ == "__main__":
    main()