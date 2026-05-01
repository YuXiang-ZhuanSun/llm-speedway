from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.config import load_config
from .runner import BenchmarkRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-speedway",
        description="Benchmark OpenAI-compatible LLM chat completion latency.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run benchmark scenarios.")
    run_parser.add_argument(
        "--config",
        default="config.json",
        help="Path to JSON config file. YAML is supported when PyYAML is installed.",
    )
    run_parser.add_argument(
        "--scenario",
        action="append",
        help="Scenario name to run. Can be passed multiple times and overrides config.scenarios.",
    )
    run_parser.add_argument(
        "--runs",
        type=int,
        help="Override benchmark.runs_per_scenario.",
    )
    run_parser.add_argument(
        "--results-dir",
        help="Override benchmark.results_dir.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        return 0

    try:
        config = load_config(Path(args.config))
        if args.scenario:
            config.scenarios = args.scenario
        if args.runs is not None:
            config.benchmark.runs_per_scenario = args.runs
        if args.results_dir:
            config.benchmark.results_dir = args.results_dir

        runner = BenchmarkRunner(config)
        report_path = runner.run()
        print(f"Benchmark finished. Report: {report_path}")
        return 0
    except KeyboardInterrupt:
        print("Benchmark interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
