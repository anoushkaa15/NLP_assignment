"""Command-line interface for the trip briefing agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import run_agent
from .grok_client import GrokAPIError
from .schemas import AgentInputError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the multi-step Grok trip briefing agent.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--request", help="Natural-language travel request.")
    input_group.add_argument("--input-file", help="Path to a text file containing the request.")
    parser.add_argument("--output", default="outputs/trip_brief.md", help="Markdown report output path.")
    parser.add_argument("--state-output", default="outputs/state.json", help="JSON state output path.")
    parser.add_argument("--trace", action="store_true", help="Print step inputs/outputs for demo explanation.")
    parser.add_argument("--mock-llm", action="store_true", help="Use deterministic local LLM responses for smoke tests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_request = args.request if args.request is not None else Path(args.input_file).read_text(encoding="utf-8")

    try:
        run_agent(
            raw_request,
            mock_llm=args.mock_llm,
            trace=args.trace,
            output_path=args.output,
            state_output_path=args.state_output,
        )
    except (AgentInputError, GrokAPIError) as exc:
        print(f"Agent failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
