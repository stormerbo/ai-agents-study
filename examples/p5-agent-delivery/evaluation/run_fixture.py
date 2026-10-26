from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline synthetic P5 evaluation fixture; makes no model/network calls.")
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--run-id", default="fixture-run")
    parser.add_argument("--state-root", type=Path, help="Required persistent fixture-replay guard directory for --split holdout.")
    holdout_mode = parser.add_mutually_exclusive_group()
    holdout_mode.add_argument("--candidate-manifest", type=Path, help="Verify candidate provenance for an offline fixture replay; this does not execute the candidate.")
    holdout_mode.add_argument("--fixture-only", action="store_true", help="Explicitly run the offline synthetic fixture without a candidate manifest.")
    args = parser.parse_args()
    if args.split == "holdout" and not (args.candidate_manifest or args.fixture_only):
        parser.error("--split holdout requires --candidate-manifest or explicit --fixture-only")
    if args.split == "dev" and (args.candidate_manifest or args.fixture_only):
        parser.error("holdout mode flags are only valid with --split holdout")
    root = Path(__file__).parent
    report = evaluate(
        root,
        args.split,
        run_id=args.run_id,
        state_root=args.state_root,
        candidate_manifest=args.candidate_manifest,
        fixture_only=args.fixture_only,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
